import os
import base64
import logging
import time
from functools import wraps
from typing import Dict, Any, Optional, Iterator
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(max_retries=3, initial_delay=2, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except APIError as e:
                    is_503 = getattr(e, 'code', None) == 503 or "503" in str(e)
                    if is_503 and attempt < max_retries:
                        logger.warning(f"503 UNAVAILABLE encountered. Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries})...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        raise e
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries:
                        logger.warning(f"503 UNAVAILABLE encountered. Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries})...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        raise e
            return func(*args, **kwargs)
        return wrapper
    return decorator

PREFERRED_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-flash-latest"
]

class GeminiAgent:
    def __init__(self):
        pass

    def _build_system_prompt(self, rag_data: Dict[str, Any]) -> str:
        intent = rag_data.get("intent", "")
        lang_pref = rag_data.get("language_preference", "ENGLISH")
        kb_context = rag_data.get("kb_context", "")
        farmer_context = rag_data.get("farmer_context", "")
        realtime_context = rag_data.get("realtime_context", "")
        soil_context = rag_data.get("soil_test_context", "")

        prompt = f"""You are FarmAssist, an expert agricultural AI advisor for farmers in Kerala, India.
Your goal is to provide accurate, helpful, and concise advice based on the provided context.
Language Preference: {lang_pref} (Respond strictly in this language).

Current Intent Detected: {intent}

--- KNOWLEDGE BASE CONTEXT ---
{kb_context}

--- FARMER & FARM CONTEXT ---
{farmer_context}
{soil_context}

--- REAL-TIME CONTEXT ---
{realtime_context}

Instructions:
1. If the user asks an out-of-scope question (e.g., "What is the capital of France?"), politely decline and steer them back to agriculture.
2. If the user asks a conversational question (e.g., greeting, thanks), respond naturally and politely.
3. If an image is provided, analyze the image in the context of the user's question (e.g., identifying pests, diseases, or crop health) and combine it with the knowledge base context to provide advice. If the image is blurry or unidentifiable, state that clearly.
4. Keep the response direct and practical for a farmer. Avoid generic statements unless necessary.
5. Base your agricultural advice strictly on the provided KNOWLEDGE BASE CONTEXT. If the context does not contain the answer, say that you don't have enough verified information and suggest they consult the local Krishi Bhavan.
"""
        return prompt

    def _generate_offline_kb_fallback(self, rag_data: Dict[str, Any]) -> str:
        kb_context = rag_data.get("kb_context", "").strip()
        query = rag_data.get("original_query", "").strip()
        
        if kb_context:
            return (
                f"### 🌾 FarmAssist Agricultural Advisory\n\n"
                f"{kb_context}\n\n"
                f"---\n*Verified from Kerala Agricultural University (KAU) / Package of Practices guidelines.*"
            )
        else:
            return (
                f"Thank you for reaching out to FarmAssist. For detailed guidance on **{query}**, "
                f"please consult your nearest Krishi Bhavan or agricultural officer for specific advice tailored to your farm."
            )

    def generate_response(self, rag_data: Dict[str, Any], api_key: str, image_data: Optional[str] = None) -> str:
        if not api_key:
            return self._generate_offline_kb_fallback(rag_data)

        system_prompt = self._build_system_prompt(rag_data)
        query = rag_data.get("original_query", "")
        conversation_context = rag_data.get("conversation_context", "")

        contents = []
        if conversation_context:
            contents.append(f"Conversation History:\n{conversation_context}\n")

        user_content = []
        if image_data:
            try:
                if "," in image_data:
                    image_data = image_data.split(",", 1)[1]
                image_bytes = base64.b64decode(image_data)
                user_content.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
            except Exception as e:
                logger.error(f"Failed to decode image data: {e}")

        user_content.append(types.Part.from_text(text=f"User Query: {query}"))
        contents.append(types.Content(role="user", parts=user_content))

        client = genai.Client(api_key=api_key)

        for model_name in PREFERRED_MODELS:
            try:
                logger.info(f"Attempting Gemini generation with model: {model_name}")
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.3,
                    )
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}. Trying fallback model...")
                time.sleep(0.5)

        logger.warning("All Gemini online models failed/exhausted. Using offline KB fallback.")
        return self._generate_offline_kb_fallback(rag_data)

    def generate_response_stream(self, rag_data: Dict[str, Any], api_key: str, image_data: Optional[str] = None) -> Iterator[str]:
        if not api_key:
            yield self._generate_offline_kb_fallback(rag_data)
            return

        system_prompt = self._build_system_prompt(rag_data)
        query = rag_data.get("original_query", "")
        conversation_context = rag_data.get("conversation_context", "")

        contents = []
        if conversation_context:
            contents.append(f"Conversation History:\n{conversation_context}\n")

        user_content = []
        if image_data:
            try:
                if "," in image_data:
                    image_data = image_data.split(",", 1)[1]
                image_bytes = base64.b64decode(image_data)
                user_content.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
            except Exception as e:
                logger.error(f"Failed to decode image data: {e}")

        user_content.append(types.Part.from_text(text=f"User Query: {query}"))
        contents.append(types.Content(role="user", parts=user_content))

        client = genai.Client(api_key=api_key)

        for model_name in PREFERRED_MODELS:
            try:
                logger.info(f"Attempting Gemini streaming with model: {model_name}")
                response_stream = client.models.generate_content_stream(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.3,
                    )
                )
                streamed_any = False
                for chunk in response_stream:
                    if chunk.text:
                        streamed_any = True
                        yield chunk.text
                if streamed_any:
                    return
            except Exception as e:
                logger.warning(f"Model {model_name} streaming failed: {e}. Trying fallback model...")
                time.sleep(0.5)

        logger.warning("All Gemini streaming models failed/exhausted. Yielding offline KB fallback.")
        yield self._generate_offline_kb_fallback(rag_data)

gemini_agent = GeminiAgent()

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
import logging
import os
import uuid
import shutil
import json
import asyncio
from fastapi.responses import StreamingResponse

from ..database import get_db
from .auth import get_current_farmer
from ..chatbot.rag_engine import rag_engine
from ..chatbot.response_generator import response_generator
from ..chatbot.voice_processor import voice_processor
from ..chatbot.tts_engine import tts_engine

router = APIRouter(prefix="/chatbot", tags=["AI Farming Consultant Agent"])
logger = logging.getLogger(__name__)

# Create temporary upload directory for voice recordings
TEMP_VOICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "temp_voice"))

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4000)
    language: Optional[str] = "AUTO"
    tts_preference: Optional[str] = "AUTO"
    image_data: Optional[str] = None

class ChatResponse(BaseModel):
    # New expanded response fields
    answer: str
    detected_language: str
    normalized_query: str
    intent: str
    confidence: float
    sources: List[str]
    retrieval_score: float
    crop_entity: Optional[str] = None
    tts_config: dict
    
    # Backward compatibility fields (mapping to old React frontend usage)
    response: str
    source: str
    matched_topic: str

class FeedbackRequest(BaseModel):
    query: str
    response: str
    intent: Optional[str] = None
    crop_entity: Optional[str] = None
    rating: int
    comment: Optional[str] = None

@router.post("/feedback")
def submit_feedback(
    request: FeedbackRequest,
    current_farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    from ..models import ChatFeedback
    new_feedback = ChatFeedback(
        farmer_id=current_farmer.id,
        query=request.query,
        response=request.response,
        intent=request.intent,
        crop_entity=request.crop_entity,
        rating=request.rating,
        comment=request.comment
    )
    db.add(new_feedback)
    db.commit()
    return {"message": "Feedback submitted successfully"}

from ..schemas import ChatFeedbackResponse

@router.get("/feedback-history", response_model=List[ChatFeedbackResponse])
def get_feedback_history(
    current_farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    from ..models import ChatFeedback
    feedback = db.query(ChatFeedback).filter(ChatFeedback.farmer_id == current_farmer.id).order_by(ChatFeedback.created_at.desc()).all()
    return feedback

@router.post("/chat", response_model=ChatResponse)
def consult_agricultural_advisor(
    request: ChatRequest,
    current_farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    try:
        rag_result = rag_engine.process_query(
            query=request.message,
            db=db,
            farmer=current_farmer,
            api_key=None
        )
        if request.language in {"ENGLISH", "MALAYALAM"}:
            rag_result["language_preference"] = request.language
            rag_result["detected_language"] = request.language
        answer = response_generator.generate_response(rag_data=rag_result, api_key=None, image_data=request.image_data)
        tts_config = tts_engine.get_speech_config(
            text=answer,
            detected_language=rag_result["detected_language"],
            preference=request.tts_preference or "AUTO"
        )
    except Exception:
        logger.exception("Chatbot request failed during processing")
        raise HTTPException(status_code=502, detail="The agricultural assistant is temporarily unavailable.")
    
    # Save the dialogue exchange in the session memory
    rag_engine.save_session_response(
        farmer_id=current_farmer.id if current_farmer else 0,
        user_query=request.message,
        bot_response=answer
    )
    
    # 4. Construct response
    first_source = rag_result["sources"][0] if rag_result["sources"] else ""
    
    return ChatResponse(
        answer=answer,
        detected_language=rag_result["detected_language"],
        normalized_query=rag_result["normalized_query"],
        intent=rag_result["intent"],
        confidence=rag_result["intent_confidence"],
        sources=rag_result["sources"],
        retrieval_score=rag_result["retrieval_score"],
        crop_entity=rag_result["crop_entity"],
        tts_config=tts_config,
        # Map to original fields to prevent breaking the frontend
        response=answer,
        source=first_source,
        matched_topic=rag_result["intent"]
    )

@router.post("/stream")
async def consult_agricultural_advisor_stream(
    request: ChatRequest,
    current_farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    try:
        rag_result = rag_engine.process_query(
            query=request.message,
            db=db,
            farmer=current_farmer,
            api_key=None
        )
        if request.language in {"ENGLISH", "MALAYALAM"}:
            rag_result["language_preference"] = request.language
            rag_result["detected_language"] = request.language
    except Exception:
        logger.exception("Chatbot request failed during RAG processing")
        raise HTTPException(status_code=502, detail="The agricultural assistant is temporarily unavailable.")
    
    async def generate_sse():
        # First chunk: yield the ContextPayload containing detected intent & real-time context
        context_payload = {
            "type": "context",
            "intent": rag_result["intent"],
            "crop_entity": rag_result.get("crop_entity"),
            "realtime_context": rag_result.get("realtime_context"),
            "sources": rag_result.get("sources", []),
            "detected_language": rag_result.get("detected_language")
        }
        yield f"data: {json.dumps(context_payload)}\n\n"
        await asyncio.sleep(0.01)

        # Subsequent chunks: yield text tokens from Gemini stream
        full_answer = ""
        try:
            for chunk in response_generator.generate_response_stream(rag_data=rag_result, api_key=None, image_data=request.image_data):
                token_payload = {
                    "type": "token",
                    "text": chunk
                }
                full_answer += chunk
                yield f"data: {json.dumps(token_payload)}\n\n"
                await asyncio.sleep(0.01)
        except Exception as e:
            logger.exception("Error during streaming generation")
            yield f"data: {json.dumps({'type': 'token', 'text': ' [Stream Error]'})}\n\n"

        # Save the dialogue exchange in the session memory once done
        rag_engine.save_session_response(
            farmer_id=current_farmer.id if current_farmer else 0,
            user_query=request.message,
            bot_response=full_answer
        )

        # Final chunk: denote stream completion
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    return StreamingResponse(generate_sse(), media_type="text/event-stream")

@router.post("/voice", response_model=ChatResponse)
def consult_advisor_via_voice(
    file: UploadFile = File(...),
    language: Optional[str] = Form("AUTO"),
    tts_preference: Optional[str] = Form("AUTO"),
    current_farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    # Ensure temporary upload directory exists
    os.makedirs(TEMP_VOICE_DIR, exist_ok=True)
    
    # Save the file with a unique name
    file_extension = os.path.splitext(file.filename)[1] or ".wav"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(TEMP_VOICE_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.exception("Failed to save uploaded audio")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to process the audio upload.")
        
    # Process voice file to transcribe
    try:
        transcription_res = voice_processor.transcribe_audio(file_path)
        transcript = transcription_res["transcript"]
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.exception("Audio transcription failed")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unable to understand the uploaded audio.")
    finally:
        # Clean up temporary voice file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
    # Run the RAG and LLM pipeline on the transcribed text
    try:
        rag_result = rag_engine.process_query(
            query=transcript,
            db=db,
            farmer=current_farmer,
            api_key=None
        )
        if language in {"ENGLISH", "MALAYALAM"}:
            rag_result["language_preference"] = language
            rag_result["detected_language"] = language
        answer = response_generator.generate_response(rag_data=rag_result, api_key=None)
        tts_config = tts_engine.get_speech_config(
            text=answer,
            detected_language=rag_result["detected_language"],
            preference=tts_preference or "AUTO"
        )
    except Exception:
        logger.exception("Voice chatbot request failed during processing")
        raise HTTPException(status_code=502, detail="The agricultural assistant is temporarily unavailable.")
    
    # Save the dialogue exchange in the session memory
    rag_engine.save_session_response(
        farmer_id=current_farmer.id if current_farmer else 0,
        user_query=transcript,
        bot_response=answer
    )
    
    first_source = rag_result["sources"][0] if rag_result["sources"] else ""
    
    return ChatResponse(
        answer=answer,
        detected_language=rag_result["detected_language"],
        normalized_query=rag_result["normalized_query"],
        intent=rag_result["intent"],
        confidence=rag_result["intent_confidence"],
        sources=rag_result["sources"],
        retrieval_score=rag_result["retrieval_score"],
        crop_entity=rag_result["crop_entity"],
        tts_config=tts_config,
        # Map to original fields for frontend compatibility
        response=answer,
        source=first_source,
        matched_topic=rag_result["intent"]
    )

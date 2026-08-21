import requests
from typing import Dict, Any

class ResponseGenerator:
    def generate_response(self, rag_data: Dict[str, Any], api_key: str = None) -> str:
        """
        Generates a natural-language grounded response using Gemini API or offline fallbacks.
        Bypasses RAG for conversational intents.
        """
        intent = rag_data["intent"]
        lang_pref = rag_data["language_preference"]
        original_query = rag_data["original_query"]
        kb_context = rag_data["kb_context"]
        farmer_context = rag_data["farmer_context"]
        conversation_context = rag_data["conversation_context"]
        realtime_context = rag_data.get("realtime_context", "")
        bypass_rag = rag_data.get("bypass_rag", False)
        
        # 1. HANDLE CONVERSATIONAL INTENTS DIRECTLY (Bypassing RAG)
        if bypass_rag:
            if lang_pref == "MALAYALAM":
                conversational_responses = {
                    "GREETING": "നമസ്കാരം! ഞാൻ ഫാം അസിസ്റ്റന്റ് ആണ്. കൃഷിയുമായി ബന്ധപ്പെട്ട എന്ത് കാര്യങ്ങളും ചോദിക്കാം. ഇന്ന് ഞാൻ എങ്ങനെയാണ് സഹായിക്കേണ്ടത്?",
                    "GOODBYE": "ശരി, വീണ്ടും കാണാം! നല്ലൊരു കാർഷിക ദിവസം ആശംസിക്കുന്നു.",
                    "THANKS": "വളരെ നന്ദി! സഹായിക്കാൻ കഴിഞ്ഞതിൽ സന്തോഷം.",
                    "CONFIRMATION": "ശരി, മനസ്സിലായി 😊. മറ്റെന്തെങ്കിലും അറിയണമെന്നുണ്ടോ?",
                    "CASUAL_CONVERSATION": "ഞാൻ സുഖമായിരിക്കുന്നു! നിങ്ങളുടെ കാർഷിക കാര്യങ്ങൾ എങ്ങനെ പോകുന്നു?"
                }
            else: # DEFAULT IS ENGLISH
                conversational_responses = {
                    "GREETING": "Hello! I'm FarmAssist, your virtual agricultural advisor. You can ask me anything about crops, soil health, fertilizers, market prices, or diseases in Kerala. How can I help you today?",
                    "GOODBYE": "Goodbye! Have a great farming day. Let me know if you need assistance later.",
                    "THANKS": "You're welcome! Glad I could help you.",
                    "CONFIRMATION": "Got it! Understood 😊. What else would you like to discuss?",
                    "CASUAL_CONVERSATION": "I'm doing great! How is your farming season going? Let me know if you have any questions."
                }
            return conversational_responses.get(intent, "Hello! How can I help you today?")

        # 2. HANDLE UNKNOWN OR OUT-OF-DOMAIN QUESTIONS
        if intent == "UNKNOWN":
            if lang_pref == "MALAYALAM":
                return (
                    "ക്ഷമിക്കണം, ഞാൻ ഒരു കാർഷിക സഹായിയായി മാത്രമാണ് രൂപകൽപ്പന ചെയ്തിരിക്കുന്നത്. "
                    "ദയവായി കൃഷിയുമായി ബന്ധപ്പെട്ട ചോദ്യങ്ങൾ ചോദിക്കുക."
                )
            else:
                return (
                    "I am sorry, but I am designed primarily as an agricultural decision support assistant. "
                    "Please ask me queries related to farming, crop health, fertilizers, or market prices in Kerala."
                )

        # 3. CALL GEMINI API (ONLINE MODE)
        if api_key:
            try:
                system_instructions = (
                    "You are FarmAssist, a friendly and realistic agricultural assistant for farmers in Kerala.\n"
                    "Your goal is to answer queries naturally and dynamically based on the contexts provided.\n\n"
                    "CRITICAL GUIDELINES:\n"
                    "1. DO NOT output any technical/formatting headers like 'Topic:', 'Article Title:', 'English Content:', 'Knowledge Base Guidelines:' in your response. Speak naturally and directly to the farmer.\n"
                    "2. Ground all chemical and biological pest treatments/dosages strictly in the provided 'Agri Knowledge Base Context'. Do not hallucinate chemical values.\n"
                    "3. Personalize your response using the 'Farmer Profile Context' (soil test parameters, location, history) ONLY when relevant to the question. Do not state random profile details if they are unrelated.\n"
                    "4. Include 'Real-Time Context' (such as current weather or market prices) dynamically if they are provided.\n"
                    "5. Respect 'Conversation Context History' for pronouns (e.g. if the user says 'leaves are yellow' after saying 'I am growing banana', recognize they mean banana leaves).\n"
                    "6. LANGUAGE POLICY:\n"
                    f"   - Respond in English by default. (Target preference: {lang_pref})\n"
                    f"   - If the target preference is MALAYALAM, translate the response to clear, friendly Malayalam.\n"
                    "7. If the retrieved context is insufficient to answer the query, advise checking with a local Krishi Bhavan rather than inventing facts."
                )
                
                prompt = (
                    f"Conversation History:\n{conversation_context}\n\n"
                    f"Farmer Profile Metrics:\n{farmer_context}\n\n"
                    f"Agri Knowledge Base Context:\n{kb_context}\n\n"
                    f"Real-Time Metrics:\n{realtime_context}\n\n"
                    f"Farmer Query: {original_query}\n\n"
                    f"Target Language: {lang_pref}\n"
                    f"Intent: {intent}"
                )
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"System Guidelines:\n{system_instructions}\n\nQuery Payload:\n{prompt}"
                        }]
                    }]
                }
                
                response = requests.post(url, json=payload, timeout=12)
                if response.status_code == 200:
                    resp_json = response.json()
                    answer = resp_json['candidates'][0]['content']['parts'][0]['text']
                    return answer.strip()
                else:
                    print(f"Gemini LLM API status error: {response.status_code}. Falling back.")
            except Exception as e:
                print(f"Gemini LLM generation failed: {e}. Falling back.")

        # 4. OFFLINE / FALLBACK MODE (RULE-BASED TEMPLATE GENERATOR)
        # Synthesize a clean, natural response without headers
        if kb_context:
            # Extract basic content
            lines = kb_context.split('\n')
            title = "Agricultural Guidelines"
            content_desc = ""
            malayalam_desc = ""
            for idx, line in enumerate(lines):
                if line.startswith("Document Title:"):
                    title = line.replace("Document Title:", "").strip()
                if line.startswith("English Content:"):
                    content_desc = line.replace("English Content:", "").strip()
                if line.startswith("Malayalam Content:"):
                    malayalam_desc = line.replace("Malayalam Content:", "").strip()
            
            # Formulate response
            if lang_pref == "MALAYALAM":
                ans = f"നിങ്ങളുടെ ചോദ്യത്തിന് കാർഷിക സർവകലാശാല നിർദ്ദേശങ്ങൾ താഴെ നൽകുന്നു:\n\n{malayalam_desc or content_desc}"
                if realtime_context:
                    ans = f"{realtime_context}\n\n{ans}"
                if farmer_context:
                    ans = f"{ans}\n\n(കുറിപ്പ്: നിങ്ങളുടെ ഫാം പ്രൊഫൈൽ വിവരങ്ങളായ {farmer_context.replace('\n', ', ')} അടിസ്ഥാനമാക്കിയുള്ളതാണ്)."
                return ans
            else:
                ans = f"Based on verified guidelines for {title}:\n\n{content_desc}"
                if realtime_context:
                    ans = f"{realtime_context}\n\n{ans}"
                if farmer_context:
                    ans = f"{ans}\n\n(Note: This advice is personalized to your profile: {farmer_context.replace('\n', ', ')})."
                return ans

        # Default empty search response
        if lang_pref == "MALAYALAM":
            return (
                "ക്ഷമിക്കണം, എന്റെ കയ്യിലുള്ള വിവരങ്ങൾ ഉപയോഗിച്ച് ഈ ചോദ്യത്തിന് കൃത്യമായ ഉത്തരം നൽകാൻ കഴിഞ്ഞില്ല. "
                "ദയവായി തദ്ദേശ കൃഷിഭവൻ സന്ദർശിക്കുക."
            )
        else:
            return (
                "I couldn't find a matching recommendation in our knowledge base. "
                "Please verify your query spelling or contact your local Krishi Bhavan."
            )

response_generator = ResponseGenerator()

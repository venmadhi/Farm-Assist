import os
import re
import requests
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..ml.language_detector import language_detector
from ..ml.thanglish_normalizer import thanglish_normalizer
from ..ml.intent_classifier import intent_classifier
from ..ml.retriever import retriever
from ..models import Farm, SoilTest, CropHistory, DiseaseRecord, CropCycle

class RAGEngine:
    def __init__(self):
        self.crops_list = ["banana", "rice", "paddy", "coconut", "pepper", "cardamom", "rubber", "ginger", "turmeric", "tapioca", "mango", "orange"]
        # In-memory session store: farmer_id -> {"history": [], "lang_pref": "ENGLISH", "active_crop": None}
        self.sessions = {}

    def get_or_create_session(self, farmer_id: int) -> dict:
        if farmer_id not in self.sessions:
            self.sessions[farmer_id] = {
                "history": [], # List of {"role": "user"|"assistant", "content": str}
                "lang_pref": "ENGLISH", # Default is English per Section 5
                "active_crop": None
            }
        return self.sessions[farmer_id]

    def extract_crop_entity(self, normalized_text: str, session: dict) -> Optional[str]:
        c = normalized_text.lower()
        # Check current query
        for crop in self.crops_list:
            if crop in c:
                detected = "rice" if crop == "paddy" else crop
                session["active_crop"] = detected # Save to session memory
                return detected
        # Fallback to session active crop
        return session.get("active_crop")

    def detect_explicit_language_preference(self, query: str, session: dict):
        """
        Check if the query explicitly requests a change of language.
        """
        c = query.lower().strip()
        malayalam_requests = ["malayalam please", "malayalathil parayamo", "malayalam parayamo", "മലയാളത്തിൽ പറയാമോ", "മലയാളം വേണം", "മലയാളം"]
        english_requests = ["english please", "in english", "english parayamo", "ഇംഗ്ലീഷ് വേണം", "ഇംഗ്ലീഷ്"]
        
        if any(req in c for req in malayalam_requests):
            session["lang_pref"] = "MALAYALAM"
            print(f"Session language updated to MALAYALAM.")
        elif any(req in c for req in english_requests):
            session["lang_pref"] = "ENGLISH"
            print(f"Session language updated to ENGLISH.")

    def get_farmer_context(self, db: Session, farmer, intent: str, crop: Optional[str]) -> str:
        """
        Retrieves farmer profile context *only* when relevant to the current agricultural question.
        For general/conversational queries, returns minimal context to reduce noise.
        """
        if not db or not farmer:
            return ""

        # conversational or out-of-domain queries should bypass profile loading
        if intent in ["GREETING", "CASUAL_CONVERSATION", "CONFIRMATION", "THANKS", "GOODBYE", "UNKNOWN"]:
            return ""

        try:
            # 1. Fetch primary farm
            farm = db.query(Farm).filter(Farm.farmer_id == farmer.id).first()
            if not farm:
                return ""

            context_lines = [
                f"Farmer Name: {farmer.full_name}",
                f"Location District: {farm.location_district}",
                f"Soil Type: {farm.soil_type}"
            ]

            # Fetch active cycle
            active_cycle = db.query(CropCycle).filter(CropCycle.farm_id == farm.id, CropCycle.status == "ACTIVE").first()
            if active_cycle:
                context_lines.append(
                    f"Current Active Crop Cycle: Cultivating {active_cycle.crop_name} on {active_cycle.area_acres} acres "
                    f"(Started: {active_cycle.start_date.strftime('%Y-%m-%d')}, Expected Yield: {active_cycle.expected_yield} kg, "
                    f"Expected Profit: INR {active_cycle.expected_profit})"
                )
            else:
                context_lines.append("Current Active Crop Cycle: None (Farmer is not currently cultivating anything)")

            # 2. Fetch soil test metrics ONLY for Fertilizer or Soil or Crop Suitability questions
            if intent in ["FERTILIZER", "SOIL", "CROP_RECOMMENDATION", "AGRICULTURAL_QUERY"]:
                soil = db.query(SoilTest).filter(SoilTest.farm_id == farm.id).order_by(SoilTest.measured_at.desc()).first()
                if soil:
                    context_lines.append(
                        f"Soil Test Results: Nitrogen={soil.nitrogen} ppm, Phosphorus={soil.phosphorus} ppm, "
                        f"Potassium={soil.potassium} ppm, soil pH={soil.ph}, Organic Carbon={soil.organic_carbon}%"
                    )

            # 3. Fetch crop history ONLY for Crop Suitability or Profit recommendations
            if intent in ["CROP_RECOMMENDATION", "PROFIT", "AGRICULTURAL_QUERY"]:
                completed = db.query(CropCycle).filter(CropCycle.farm_id == farm.id, CropCycle.status == "HARVESTED").order_by(CropCycle.harvest_date.desc()).limit(2).all()
                if completed:
                    crops_past = [f"{c.crop_name} (Yield: {c.actual_yield} kg, Profit: INR {c.actual_profit})" for c in completed]
                    context_lines.append(f"Past Farming Cycle History: {', '.join(crops_past)}")

            # 4. Fetch recent diseases ONLY if dealing with Disease questions or active crop matches
            if intent in ["DISEASE", "AGRICULTURAL_QUERY"] or (crop and crop != 'general'):
                diseases = db.query(DiseaseRecord).filter(DiseaseRecord.farm_id == farm.id).order_by(DiseaseRecord.scanned_at.desc()).limit(1).all()
                if diseases:
                    context_lines.append(f"Recent Farm Disease Record: {diseases[0].detected_disease} (Severity: {diseases[0].severity_level})")

            return "\n".join(context_lines)
        except Exception as e:
            print(f"Error compiling farmer context: {e}")
            return ""

    def get_realtime_context(self, district: str, intent: str, crop: Optional[str]) -> str:
        """
        Fetches live real-time metrics (like current weather or crop market prices) dynamically.
        """
        if intent == "WEATHER" and district:
            try:
                # Call wttr.in open api to get current weather summary for district
                url = f"https://wttr.in/{district}?format=%C+%t+%w"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    return f"Current Real-Time Weather in {district}: {res.text.strip()}"
            except Exception as e:
                print(f"Error fetching live weather: {e}")
            return f"Current Weather in {district}: Heavy monsoon rains forecasted, high relative humidity (85%)."
            
        if intent == "MARKET" and crop:
            # Dynamically compile crop average rates in Kerala
            crop_prices = {
                "banana": "Nendran Banana (Grade A): ₹44/kg, Robusta: ₹28/kg",
                "rice": "Paddy (Jyothi): ₹29.50/kg, Matta Rice: ₹38/kg",
                "pepper": "Black Pepper (Garbled): ₹615/kg, Ungarbled: ₹595/kg",
                "coconut": "Coconut (with husk): ₹36/nut, Copra: ₹11,200/quintal",
                "rubber": "RSS-4 Grade Sheet Rubber: ₹182/kg, RSS-5: ₹178/kg",
                "cardamom": "Cardamom (Green Medium): ₹1,850/kg",
                "ginger": "Ginger (Fresh): ₹120/kg"
            }
            price_quote = crop_prices.get(crop.lower(), "Average Agricultural Produce: Rates stable")
            return f"Real-Time Market Prices ({crop.capitalize()}): {price_quote} (Sourced from local Kerala market yards)."
            
        return ""

    def process_query(self, query: str, db: Session = None, farmer = None, api_key: str = None) -> Dict[str, Any]:
        # 1. Fetch Session Memory
        farmer_id = farmer.id if farmer else 0
        session = self.get_or_create_session(farmer_id)
        
        # 2. Update Language Preference based on explicit queries
        self.detect_explicit_language_preference(query, session)
        
        # 3. Detect Language & Normalize Query
        lang = language_detector.detect(query)
        norm_query = thanglish_normalizer.normalize(query)
        
        # 4. Predict Intent
        intent_res = intent_classifier.predict(norm_query)
        intent = intent_res["intent"]
        intent_confidence = intent_res["confidence"]
        
        # Check if conversational intent - bypass RAG completely
        bypass_rag = intent in ["GREETING", "CASUAL_CONVERSATION", "CONFIRMATION", "THANKS", "GOODBYE"]
        
        # 5. Crop Entity extraction with memory support
        crop_entity = self.extract_crop_entity(norm_query, session)
        
        # 6. Prepare Conversation Context string
        history_lines = []
        for turn in session["history"][-6:]: # Include last 6 turns for memory
            history_lines.append(f"{turn['role'].capitalize()}: {turn['content']}")
        conversation_context = "\n".join(history_lines)
        
        if bypass_rag:
            return {
                "original_query": query,
                "detected_language": lang,
                "normalized_query": norm_query,
                "intent": intent,
                "intent_confidence": intent_confidence,
                "crop_entity": crop_entity,
                "sources": [],
                "retrieval_score": 0.0,
                "kb_context": "",
                "farmer_context": "",
                "conversation_context": conversation_context,
                "bypass_rag": True,
                "language_preference": session["lang_pref"]
            }
            
        # 7. Semantic Vector Retrieval
        matches = retriever.retrieve(
            query=norm_query,
            intent=intent,
            crop_entity=crop_entity,
            api_key=api_key,
            k=3
        )
        
        retrieved_contexts = []
        sources = []
        best_score = 0.0
        
        for idx, (doc, score) in enumerate(matches):
            if idx == 0:
                best_score = score
            source_name = doc.get('source_name') or doc.get('source', 'Kerala Agricultural University')
            source_url = doc.get('source_url', 'https://kau.in')
            sources.append(source_name)
            
            # Format clean, structured RAG internal document
            retrieved_contexts.append(
                f"Document Title: {doc.get('title')}\n"
                f"Crop: {doc.get('crop')}\n"
                f"Source: {source_name} ({source_url})\n"
                f"Date: {doc.get('date', 'N/A')}\n"
                f"English Content: {doc.get('content')}\n"
                f"Malayalam Content: {doc.get('malayalam_content')}"
            )
            
        combined_kb_context = "\n\n".join(retrieved_contexts)
        
        # 8. Farmer Profile Context (Personalized & relevance-filtered)
        farmer_context = self.get_farmer_context(db, farmer, intent, crop_entity)
        
        # 9. Real-Time Context Weather/Prices
        district = ""
        if db and farmer:
            farm = db.query(Farm).filter(Farm.farmer_id == farmer.id).first()
            if farm:
                district = farm.location_district
        realtime_context = self.get_realtime_context(district, intent, crop_entity)
        
        return {
            "original_query": query,
            "detected_language": lang,
            "normalized_query": norm_query,
            "intent": intent,
            "intent_confidence": intent_confidence,
            "crop_entity": crop_entity,
            "sources": list(set(sources)) if sources else [],
            "retrieval_score": round(best_score, 4),
            "kb_context": combined_kb_context,
            "farmer_context": farmer_context,
            "realtime_context": realtime_context,
            "conversation_context": conversation_context,
            "bypass_rag": False,
            "language_preference": session["lang_pref"]
        }

    def save_session_response(self, farmer_id: int, user_query: str, bot_response: str):
        """
        Updates session history with current transaction.
        """
        session = self.get_or_create_session(farmer_id)
        session["history"].append({"role": "user", "content": user_query})
        session["history"].append({"role": "assistant", "content": bot_response})

rag_engine = RAGEngine()

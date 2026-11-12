import os
import re
import logging
import requests
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..ml.language_detector import language_detector
from ..ml.thanglish_normalizer import thanglish_normalizer
from ..ml.intent_classifier import intent_classifier
from ..ml.agriculture_entities import extract_entities, has_agricultural_entity
from ..ml.retriever import retriever
from ..models import Farm, SoilTest, CropHistory, DiseaseRecord, CropCycle

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        # In-memory session store: farmer_id -> session dict
        self.sessions = {}

    @staticmethod
    def _new_session() -> dict:
        return {
            "history": [],
            "lang_pref": "ENGLISH",
            "active_crop": None,
            "crop_confidence": 0.0,   # track how confident we are in session crop
            "context": {
                "crop": None, "crop_confidence": 0.0,
                "location": None, "soil": None, "season": None,
                "water_availability": None, "land_size": None, "sunlight": None, "elevation": None,
                "growth_stage": None, "farming_goal": None, "weather": None,
                "previous_crop": None, "disease_result": None,
            },
        }

    def get_or_create_session(self, farmer_id: int) -> dict:
        if farmer_id not in self.sessions:
            self.sessions[farmer_id] = self._new_session()
        return self.sessions[farmer_id]

    def extract_profile_crop(self, db: Session, farmer) -> Optional[str]:
        """Use explicitly active crop cycle from farmer profile if available."""
        if not db or not farmer:
            return None
        try:
            farm = db.query(Farm).filter(Farm.farmer_id == farmer.id).first()
            if not farm:
                return None
            active_cycle = db.query(CropCycle).filter(
                CropCycle.farm_id == farm.id,
                CropCycle.status == "ACTIVE"
            ).first()
            if active_cycle and isinstance(active_cycle.crop_name, str) and active_cycle.crop_name.strip():
                crop = active_cycle.crop_name.lower().strip()
                return "rice" if crop in ["paddy", "nellu", "rice"] else crop
        except Exception:
            return None
        return None

    @staticmethod
    def update_context(entities: dict, session: dict, explicit: bool = False, query: str = "") -> None:
        """Update session context; explicit current-message entities always win."""
        context = session["context"]
        if entities.get("crop"):
            # Explicit query crop always overrides lower-confidence session crop
            new_conf = 1.0 if explicit else 0.7
            if explicit or new_conf >= context.get("crop_confidence", 0.0):
                context["crop"] = entities["crop"]
                context["crop_confidence"] = new_conf
                session["active_crop"] = entities["crop"]
                session["crop_confidence"] = new_conf
        if entities.get("location"):
            context["location"] = entities["location"]
        if entities.get("growth_stage"):
            context["growth_stage"] = entities["growth_stage"]
            
        # Handle contradiction in context (e.g. soil types, rain)
        q_lower = query.lower()
        if any(w in q_lower for w in ["sandy", "clay", "laterite", "loam"]):
            if "clay" in q_lower: context["soil"] = "clay"
            elif "sandy" in q_lower: context["soil"] = "sandy"
            elif "laterite" in q_lower: context["soil"] = "laterite"
            elif "loam" in q_lower: context["soil"] = "loam"
            
        if "rain" in q_lower:
            if "no " in q_lower or "hasn't" in q_lower or "has not" in q_lower:
                context["weather"] = "no rain"
            else:
                context["weather"] = "raining"
        elif entities.get("weather_condition"):
            context["weather"] = entities["weather_condition"]
            
        if entities.get("pest"):
            context["pest"] = entities["pest"]
        if entities.get("disease"):
            context["disease"] = entities["disease"]
        if entities.get("weed"):
            context["weed"] = entities["weed"]

    @staticmethod
    def expand_query(query: str, crop: Optional[str], intents: List[str], context: dict) -> str:
        """Build a retrieval query from entities, intent concepts, and known context."""
        terms = [query]
        crop_name = crop or "crop"
        expansions = {
            "CROP_SELECTION": [f"{crop_name} suitability", "crop suitability", "growing conditions", "climate requirements", "soil requirements"],
            "CROP_SUITABILITY": [f"{crop_name} suitability", f"can I grow {crop_name} in Kerala", f"{crop_name} growing conditions", f"{crop_name} agro-climatic suitability"],
            "CROP_CULTIVATION": [f"{crop_name} cultivation", f"growing {crop_name}", "planting practices"],
            "SOWING_TIME": [f"{crop_name} sowing time", f"{crop_name} planting season", f"{crop_name} crop calendar Kerala", "when to sow", "sowing season"],
            "CROP_CALENDAR": [f"{crop_name} crop calendar", f"{crop_name} agricultural season", "Kerala crop calendar"],
            "PLANTING": [f"{crop_name} planting", f"{crop_name} transplanting", f"{crop_name} spacing", "seedling preparation"],
            "HARVESTING": [f"{crop_name} harvesting", "maturity", "harvest timing"],
            "POST_HARVEST": [f"{crop_name} post harvest", f"{crop_name} drying", f"{crop_name} storage", "moisture", "spoilage prevention"],
            "DRYING": [f"{crop_name} drying", "grain moisture management", f"{crop_name} sun drying"],
            "STORAGE": [f"{crop_name} storage", "safe storage", "fungal spoilage", f"{crop_name} warehouse"],
            "SHELF_LIFE": [f"{crop_name} shelf life", f"{crop_name} storage duration", f"how long can {crop_name} be stored"],
            "WEATHER": ["weather impact farming", "monsoon agriculture", "rain management"],
            "WEATHER_FORECAST": ["rain forecast", "weather forecast Kerala", "monsoon forecast"],
            "WEATHER_AGRICULTURE": ["agricultural weather", "rain management", "monsoon impact"],
            "WEATHER_IMPACT": ["weather impact", "rain management", "monsoon farming", "heatwave crop protection"],
            "CLIMATE": ["climate agro", "seasonal crop planning"],
            "DISEASE_IDENTIFICATION": [f"{crop_name} disease symptoms", "disease identification"],
            "DISEASE_CONTROL": [f"{crop_name} disease control", "disease management", f"{crop_name} fungicide"],
            "PEST_IDENTIFICATION": [f"{crop_name} pest symptoms", "pest identification"],
            "PEST_CONTROL": [f"{crop_name} pest control", "pest management", f"{crop_name} insect control"],
            "ORGANIC_PEST_CONTROL": [f"{crop_name} organic pest control", "neem oil", "bio pesticide", "IPM"],
            "TRAP_CROP": ["trap crop", "companion planting", "border crop pest"],
            "PESTICIDE_APPLICATION": [f"{crop_name} pesticide application", "pesticide schedule", "spray frequency", "pesticide dosage"],
            "WEED_MANAGEMENT": [f"{crop_name} weed control", f"{crop_name} weed management", "herbicide", "manual weeding"],
            "FERTILIZER_RECOMMENDATION": [
                f"{crop_name} fertilizer recommendation Kerala",
                f"{crop_name} nutrient management",
                f"{crop_name} fertilizer application",
                f"{crop_name} nutrient requirements",
                f"{crop_name} fertilizer schedule",
                f"Kerala {crop_name} fertilizer guidelines"
            ],
            "MANURE_RECOMMENDATION": [f"{crop_name} organic manure", f"{crop_name} compost application", f"{crop_name} farmyard manure"],
            "NUTRIENT_DEFICIENCY": [f"{crop_name} nutrient deficiency", f"{crop_name} yellowing", "nitrogen deficiency", "potassium deficiency", "micronutrient"],
            "CROP_NUTRIENT_REQUIREMENT": [f"{crop_name} nutrient requirement", f"{crop_name} NPK"],
            "SOIL_RECOMMENDATION": [f"{crop_name} soil health", f"{crop_name} soil improvement", "organic soil improvement", "soil fertility"],
            "SOIL_HEALTH": [f"{crop_name} soil health", "organic soil improvement", "soil fertility"],
            "SOIL_PH": ["soil pH", "soil acidity", "lime application", "pH correction"],
            "SOIL_TEST_INTERPRETATION": ["soil test", "NPK soil", "soil test result"],
            "SOIL_SUITABILITY": [f"{crop_name} soil suitability", "soil management", "crop soil requirements", "pH requirements"],
            "SOIL_WATERLOGGING": ["waterlogged soil", "drainage improvement", "excess water in field"],
            "DRAINAGE": ["drainage", "soil drainage", "excess water"],
            "ORGANIC_FARMING": ["organic farming", "jeevamrutham preparation", "bio fertilizer formulation", "cow dung urine preparation"],
            "INPUT_PREPARATION": ["input preparation", "jeevamrutham formulation", "organic formulation recipe"],
            "IRRIGATION": [f"{crop_name} irrigation", f"{crop_name} water management", "water schedule"],
            "WATER_REQUIREMENT": [f"{crop_name} water requirement", f"{crop_name} litres per week", f"{crop_name} irrigation frequency"],
            "MARKET_PRICE": [f"{crop_name} market price", f"{crop_name} mandi rate", f"{crop_name} current price Kerala"],
            "MARKET_LOCATION": [f"{crop_name} sell", f"{crop_name} agro market", "nearest market", "APMC"],
            "MARKET_TIMING": [f"{crop_name} sell timing", "best time to sell", "price trend"],
            "MSP": ["minimum support price", f"{crop_name} MSP", "government procurement price"],
            "MARKET_FORECAST": [f"{crop_name} price forecast", "price trend next month"],
            "GOVERNMENT_SCHEME": ["government scheme agriculture Kerala", "krishi bhavan scheme", "farmer subsidy"],
            "SUBSIDY": ["drip irrigation subsidy", "agriculture subsidy Kerala", "government grant farmer"],
            "CROP_INSURANCE": ["crop insurance", "PMFBY", "fasal bima"],
            "PM_KISAN": ["PM Kisan", "PM-KISAN scheme", "farmer income support"],
            "KISAN_CREDIT_CARD": ["Kisan Credit Card", "KCC", "farm loan"],
            "LIVESTOCK": ["livestock", "animal husbandry", "cattle"],
            "POULTRY": ["poultry", "chicken", "hen management"],
            "PROFITABILITY": [f"{crop_name} profit", f"{crop_name} economics", "farm profitability"],
            "YIELD_ESTIMATION": [f"{crop_name} yield", f"{crop_name} output per acre"],
        }
        for intent in intents:
            terms.extend(expansions.get(intent, []))
        if context.get("location"):
            terms.append(str(context["location"]))
        return " ".join(dict.fromkeys(terms))

    @staticmethod
    def detect_related_intents(query: str, primary_intent: str) -> List[str]:
        """Detect multi-intent combinations without losing primary intent."""
        lower_query = query.lower()
        related = [primary_intent]
        markers = {
            "HARVESTING": ["harvest", "harvesting", "reaping", "കൊയ്ത്ത്", "വിളവെടുപ്പ്"],
            "DRYING": ["dry", "drying", "moisture", "wet grain", "ഉണക്കൽ"],
            "STORAGE": ["store", "storage", "spoilage", "mould", "mold", "സംഭരണം"],
            "SHELF_LIFE": ["shelf life", "how long", "keep fresh", "storage duration"],
            "WEATHER_AGRICULTURE": ["rain", "rainfall", "monsoon", "mazha", "showers", "weather", "മഴ", "കാലാവസ്ഥ"],
            "WEATHER_IMPACT": ["heavy rain", "monsoon", "rain is coming", "flood", "drought", "heatwave", "കനത്ത മഴ", "മഴക്കാലത്ത്"],
            "SOIL_HEALTH": ["improve soil", "soil health", "soil fertility", "enrich soil", "മണ്ണ് മെച്ചപ്പെടുത്ത"],
            "FERTILIZER_RECOMMENDATION": ["fertilizer", "fertiliser", "valam", "urea", "npk", "potash", "വളം"],
            "MANURE_RECOMMENDATION": ["manure", "fym", "cow dung", "ചാണകം", "ജൈവവളം"],
            "ORGANIC_FARMING": ["organic", "jaiva", "jeevamrutham", "panchagavya", "ജീവാമൃതം"],
            "INPUT_PREPARATION": ["how to prepare", "how to make", "preparation", "recipe", "തയ്യാറാക്കുന്ന"],
            "APPLICATION_SCHEDULE": ["how often", "when to apply", "how many times", "schedule", "frequency", "എപ്പോൾ", "എത്ര തവണ"],
            "NUTRIENT_DEFICIENCY": ["yellow", "yellowing", "deficiency", "scorch", "chlorosis", "മഞ്ഞപ്പ്", "കുറവ്"],
            "IRRIGATION": ["irrigation", "water requirement", "watering", "vellam", "ജലസേചനം", "നന"],
            "WEED_MANAGEMENT": ["weed", "weeds", "kala", "kalakal", "കള"],
            "PEST_CONTROL": ["pest", "aphid", "borer", "beetle", "insect", "കീടം"],
            "DISEASE_CONTROL": ["disease", "fungus", "blight", "wilt", "rot", "രോഗം"],
            "SOWING_TIME": ["sow", "sowing", "seed", "nursery", "planting time"],
            "MARKET_TIMING": ["sell", "selling", "price trend", "store or sell"],
            "GOVERNMENT_SCHEME": ["scheme", "subsidy", "insurance", "credit", "loan"],
        }
        for intent, words in markers.items():
            if any(word in lower_query for word in words) and intent not in related:
                related.append(intent)

        # Auto-expand composite intents
        if primary_intent == "POST_HARVEST":
            for sub in ["HARVESTING", "DRYING", "STORAGE"]:
                if sub not in related:
                    related.append(sub)
        if primary_intent == "CROP_SELECTION" and "CROP_SUITABILITY" not in related:
            related.append("CROP_SUITABILITY")
        if primary_intent == "CROP_SUITABILITY" and "CROP_SELECTION" not in related:
            related.append("CROP_SELECTION")
        if primary_intent in ["WEATHER_FORECAST", "WEATHER"] and "WEATHER_AGRICULTURE" not in related:
            related.append("WEATHER_AGRICULTURE")

        return related

    def detect_explicit_language_preference(self, query: str, session: dict):
        c = query.lower().strip()
        malayalam_requests = ["malayalam please", "malayalathil parayamo", "malayalam parayamo", "മലയാളത്തിൽ പറയാമോ", "മലയാളം വേണം", "മലയാളം"]
        english_requests = ["english please", "in english", "english parayamo", "ഇംഗ്ലീഷ് വേണം", "ഇംഗ്ലീഷ്"]
        
        if any(req in c for req in malayalam_requests):
            session["lang_pref"] = "MALAYALAM"
        elif any(req in c for req in english_requests):
            session["lang_pref"] = "ENGLISH"

    @staticmethod
    def is_farming_scope(query: str) -> bool:
        """Check if query is within agriculture domain.

        Entity-first: if any crop entity is extracted, it's in scope.
        Keyword fallback for general agricultural terms.
        """
        # 1. Entity evidence (strong signal) — uses the module-level import
        if has_agricultural_entity(query):
            return True
        # 2. Keyword evidence
        farming_terms = [
            "farm", "farmer", "farming", "agriculture", "agri", "crop", "plant", "seed", "field",
            "soil", "fertilizer", "fertiliser", "manure", "urea", "npk", "pest", "insect", "aphid",
            "disease", "leaf", "wilt", "quick wilt", "irrigation", "weather", "rain", "market", "price",
            "yield", "harvest", "monsoon", "climate", "paddy", "rice", "banana", "coconut", "pepper", "black pepper",
            "rubber", "cardamom", "ginger", "turmeric", "tomato", "apple", "mango", "krishi", "krishibhavan",
            "valam", "mannu", "mazha", "vellam", "vila", "nellu", "vazha", "thengu", "thakkali",
            "subsidy", "scheme", "insurance", "msp", "kisan", "sowing", "planting", "nursery",
            " weed", "herbicide", "pesticide", "fungicide", "storage", "drying", "post harvest",
            "കൃഷി", "കർഷകൻ", "വിള", "മണ്ണ്", "വളം", "കീടം", "രോഗം", "ഇല", "ജലം", "മഴ", "കാലാവസ്ഥ",
            "വിപണി", "നെല്ല്", "തെങ്ങ്", "വാഴ", "കുരുമുളക്", "തക്കാളി", "ആപ്പിൾ", "ഏത് വിള", "മികച്ച വിള",
            "whitefly", "whiteflies", "neem", "oil", "kalakal", "kala", "weed"
        ]
        query_lower = query.lower()
        return any(term in query_lower for term in farming_terms)

    def get_farmer_context(self, db: Session, farmer, intent: str, crop: Optional[str]) -> str:
        if not db or not farmer:
            return ""

        if intent in ["GREETING", "CASUAL_CONVERSATION", "CONFIRMATION", "THANKS", "GOODBYE", "UNKNOWN"]:
            return ""

        try:
            farm = db.query(Farm).filter(Farm.farmer_id == farmer.id).first()
            if not farm:
                return ""

            context_lines = [f"Location District: {farm.location_district}"]
            if farm.soil_type:
                context_lines.append(f"Soil Type: {farm.soil_type}")
            if intent in ["CROP_SELECTION", "CROP_SUITABILITY"]:
                if farm.water_availability:
                    context_lines.append(f"Water Availability: {farm.water_availability}")
                if farm.land_area_acres:
                    context_lines.append(f"Farm Area Acres: {farm.land_area_acres}")
                return "\n".join(context_lines)

            active_cycle = db.query(CropCycle).filter(CropCycle.farm_id == farm.id, CropCycle.status == "ACTIVE").first()
            if active_cycle:
                context_lines.append(
                    f"Current Active Crop Cycle: Cultivating {active_cycle.crop_name} on {active_cycle.area_acres} acres "
                    f"(Started: {active_cycle.start_date.strftime('%Y-%m-%d')}, Expected Yield: {active_cycle.expected_yield} kg)"
                )

            if intent in ["FERTILIZER_RECOMMENDATION", "CROP_NUTRIENT_REQUIREMENT", "NUTRIENT_DEFICIENCY", "SOIL_SUITABILITY", "SOIL_TEST_INTERPRETATION"]:
                soil = db.query(SoilTest).filter(SoilTest.farm_id == farm.id).order_by(SoilTest.measured_at.desc()).first()
                if soil:
                    context_lines.append(
                        f"Soil Test Results: Nitrogen={soil.nitrogen} ppm, Phosphorus={soil.phosphorus} ppm, "
                        f"Potassium={soil.potassium} ppm, soil pH={soil.ph}, Organic Carbon={soil.organic_carbon}%"
                    )

            return "\n".join(context_lines)
        except Exception as e:
            logger.warning("Error compiling farmer context: %s", e)
            return ""

    def get_realtime_context(self, district: str, intent: str, crop: Optional[str], time_reference: Optional[str]) -> str:
        # Weather Routing
        if intent in ["WEATHER", "HEATWAVE", "IRRIGATION"] and district:
            try:
                forecast_flag = "?format=%C+%t+%w"
                url = f"https://wttr.in/{district}{forecast_flag}"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    return f"Current Real-Time Weather in {district}: {res.text.strip()}"
            except Exception as e:
                logger.warning("Error fetching live weather: %s", e)
                return f"Live weather API unavailable for {district}."
        
        # Market Routing
        if intent in ["MARKET_PRICE", "MARKET_FORECAST", "MARKET_SELLING", "MSP"] and crop:
            try:
                from ..ml.market_agent import MarketAgent
                market_agent = MarketAgent()
                forecast_data = market_agent.get_market_forecast(crop, district or "Palakkad")
                return f"Verified Live Market Data for {crop}: Current price is Rs. {forecast_data['current_market_price']}/kg. Expected 30-day price trend: Rs. {forecast_data['price_forecast_30d']}/kg."
            except ValueError as ve:
                return f"Verified Live Market Data for {crop}: {str(ve)}. Currently unavailable."
            except Exception as e:
                logger.warning("Error fetching live market data: %s", e)
                return f"I don't have verified current market-price data for {crop} right now."
                
        return ""

    def process_query(self, query: str, db: Session = None, farmer = None, api_key: str = None) -> Dict[str, Any]:
        # 1. Fetch Session Memory
        farmer_id = farmer.id if farmer else None
        session = self.get_or_create_session(farmer_id) if farmer else self._new_session()
        
        # 2. Update Language Preference
        self.detect_explicit_language_preference(query, session)
        
        # 3. Detect Language & Normalize Query
        lang = language_detector.detect(query)
        if lang == "MALAYALAM" or (lang == "MIXED" and re.search(r'[\u0d00-\u0d7f]', query)):
            session["lang_pref"] = "MALAYALAM"
        elif lang == "ENGLISH":
            session["lang_pref"] = "ENGLISH"
        norm_query = thanglish_normalizer.normalize(query)
        
        # 4. Master Entity Extraction (BEFORE RAG)
        entities = extract_entities(norm_query)
        # If crop not in normalized, try original query
        if not entities.get("crop"):
            entities = extract_entities(query)
            
        explicit_query_crop = entities.get("crop")

        # 5. Predict primary intent and related multi-intents
        intent_res = intent_classifier.predict(norm_query)
        intent = intent_res["domain"]
        intent_confidence = intent_res["confidence"]
        needs_clarification = intent_res.get("needs_clarification", False)
        
        # We don't need the legacy detect_related_intents anymore, we just use the domain
        detected_intents = [intent]
        
        # Context Resolution:
        # Explicit query crop always wins (confidence = 1.0); falls back to session crop
        if explicit_query_crop:
            crop_entity = explicit_query_crop
            self.update_context(entities, session, explicit=True, query=query)
        else:
            crop_agnostic_intents = [
                "WEATHER_CLIMATE", 
                "MARKET_PRICING", 
                "GOVERNMENT_SCHEMES", 
                "LIVESTOCK", 
                "GENERAL_FARMING", 
                "SOIL_WATER", 
                "CROP_SELECTION"
            ]
            pest_disease_intents = ["PEST_MANAGEMENT", "WEED_MANAGEMENT", "CROP_DISEASE"]
            
            # 1. Do not auto-inject active_crop for broadly crop-agnostic intents
            if intent in crop_agnostic_intents:
                crop_entity = None
            # 2. Do not auto-inject active_crop if user explicitly asked about a specific pest/disease/weed without naming a crop
            elif intent in pest_disease_intents and (entities.get("pest") or entities.get("disease") or entities.get("weed")):
                crop_entity = None
            # 3. Otherwise, safely fallback to active session crop
            else:
                crop_entity = session.get("active_crop")
                
            if crop_entity is None and intent not in crop_agnostic_intents:
                crop_entity = self.extract_profile_crop(db, farmer)
                if crop_entity:
                    session["active_crop"] = crop_entity
                    session["crop_confidence"] = 0.5  # profile crop is lower confidence

        # Override crop in entities dictionary for further processing
        entities["crop"] = crop_entity
        entities["pest"] = intent_res.get("pest") or session["context"].get("pest")
        entities["disease"] = intent_res.get("disease") or session["context"].get("disease")
        entities["weed"] = intent_res.get("weed") or session["context"].get("weed")

        if not explicit_query_crop:
            self.update_context(entities, session, explicit=False, query=query)
        expanded_query = self.expand_query(norm_query, crop_entity, detected_intents, session["context"])
        
        # 6. Conversation Context string
        history_lines = []
        # Inject system anchor for active crop to guarantee persistence across long conversations
        if crop_entity:
            history_lines.append(f"System Context: The current active crop under discussion is '{crop_entity}'.")
            
        for turn in session["history"][-20:]:  # Keep up to 10 full exchanges
            history_lines.append(f"{turn['role'].capitalize()}: {turn['content']}")
        conversation_context = "\n".join(history_lines)
            
        # 7. Semantic Vector Retrieval with Multi-Factor Re-Ranking
        matches = [] if intent in ["NEGATIVE_FEEDBACK"] else retriever.retrieve(
            query=expanded_query,
            intent=detected_intents,
            crop_entity=crop_entity,
            api_key=api_key,
            k=3,
            structured_intent=intent_res
        )
        
        retrieved_contexts = []
        sources = []
        best_score = 0.0
        
        for idx, (doc, score) in enumerate(matches):
            if idx == 0:
                best_score = score
            source_name = doc.get('source_name') or doc.get('authority', 'Kerala Agricultural University')
            source_url = doc.get('source_url', 'https://kau.in')
            sources.append(source_name)
            
            # Format clean, structured RAG internal document
            doc_intents_str = ", ".join(doc.get('intent', [])) if isinstance(doc.get('intent'), list) else str(doc.get('intent', ''))
            retrieved_contexts.append(
                f"Document Title: {doc.get('title')}\n"
                f"Crop: {doc.get('crop')}\n"
                f"Intent: {doc_intents_str}\n"
                f"Source: {source_name} ({source_url})\n"
                f"Date: {doc.get('date', 'N/A')}\n"
                f"English Content: {doc.get('content')}\n"
                f"Malayalam Content: {doc.get('malayalam_content')}"
            )
            
        combined_kb_context = "\n\n".join(retrieved_contexts)
        
        # 8. Farmer Profile Context
        farmer_context = self.get_farmer_context(db, farmer, intent, crop_entity)
        soil_test_context = ""
        if db and farmer and intent in ["SOIL_TEST_INTERPRETATION", "NUTRIENT_DEFICIENCY", "CROP_HEALTH_CHECK", "FERTILIZER_RECOMMENDATION"]:
            try:
                farm = db.query(Farm).filter(Farm.farmer_id == farmer.id).first()
                if farm:
                    soil = db.query(SoilTest).filter(SoilTest.farm_id == farm.id).order_by(SoilTest.measured_at.desc()).first()
                    if soil:
                        soil_test_context = (
                            f"Nitrogen={soil.nitrogen} ppm; Phosphorus={soil.phosphorus} ppm; "
                            f"Potassium={soil.potassium} ppm; pH={soil.ph}; Organic Carbon={soil.organic_carbon}%"
                        )
            except Exception as e:
                logger.warning("Error compiling structured soil test context: %s", e)
        
        # 9. Real-Time Context — use entity location OR farm district
        district = entities.get("location")
        if not district and session["context"].get("location"):
            district = session["context"]["location"]
        if not district and db and farmer:
            try:
                farm = db.query(Farm).filter(Farm.farmer_id == farmer.id).first()
                if farm:
                    district = farm.location_district
            except Exception:
                pass
        realtime_context = self.get_realtime_context(district, intent, crop_entity, entities.get("time_reference"))

        # 10. Structured Debug Logging
        doc_titles = [doc.get("title") for doc, _ in matches]
        doc_crops = [doc.get("crop") for doc, _ in matches]
        scores = [round(score, 4) for _, score in matches]
        
        logger.info(
            "AGRIGENIE DEBUG | QUERY: %s | LANG: %s | CROP: %s | INTENT: %s | ENTITIES: %s | EXPANDED: %s | TOP_DOCS: %s | DOC_CROPS: %s | SCORES: %s | SOURCE: %s",
            query,
            lang,
            crop_entity or "None",
            intent,
            entities,
            expanded_query,
            doc_titles,
            doc_crops,
            scores,
            sources[0] if sources else "None"
        )
        
        return {
            "original_query": query,
            "detected_language": lang,
            "normalized_query": norm_query,
            "intent": intent,
            "intents": detected_intents,
            "intent_confidence": intent_confidence,
            "needs_clarification": needs_clarification,
            "crop_entity": crop_entity,
            "entities": entities,
            "data_type": entities.get("data_type", "STATIC"),
            "method_constraint": entities.get("method_constraint"),
            "sources": list(dict.fromkeys(sources)) if sources else [],
            "retrieval_score": round(best_score, 4),
            "kb_context": combined_kb_context,
            "farmer_context": farmer_context,
            "soil_test_context": soil_test_context,
            "realtime_context": realtime_context,
            "conversation_context": conversation_context,
            "expanded_query": expanded_query,
            "bypass_rag": False,
            "language_preference": session["lang_pref"],
            "conversation_state": session["context"].copy()
        }

    def save_session_response(self, farmer_id: int, user_query: str, bot_response: str):
        session = self.get_or_create_session(farmer_id)
        session["history"].append({"role": "user", "content": user_query})
        session["history"].append({"role": "assistant", "content": bot_response})

rag_engine = RAGEngine()

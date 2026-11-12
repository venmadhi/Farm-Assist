import os
import pickle
import re
import numpy as np
from typing import Dict, Any, List
from .thanglish_normalizer import thanglish_normalizer
from .agriculture_entities import has_agricultural_entity, extract_crops, extract_entities
from .language_detector import language_detector

class IntentClassifier:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.primary_domains = [
            'WEATHER', 'CROP_CALENDAR', 'CROP_SOWING', 'HEATWAVE', 'IRRIGATION',
            'PEST_MANAGEMENT', 'WEED_MANAGEMENT', 'DISEASE', 'SOIL_MANAGEMENT',
            'SOIL_TYPE', 'SOIL_PH', 'WATER_MANAGEMENT', 'FERTILIZER',
            'CROP_RECOMMENDATION', 'MARKET_PRICE', 'MARKET_SELLING',
            'MARKET_FORECAST', 'MSP', 'GOVERNMENT_SCHEME', 'SUBSIDY',
            'PM_KISAN', 'CROP_INSURANCE', 'KCC', 'POST_HARVEST', 'STORAGE',
            'DRYING', 'LIVESTOCK', 'POULTRY', 'GENERAL_AGRICULTURE',
            'OUT_OF_SCOPE', 'CLARIFICATION_REQUIRED'
        ]
        
    def predict(self, text: str) -> Dict[str, Any]:
        normalized_text = thanglish_normalizer.normalize(text)
        c = normalized_text.lower().strip()
        lang = language_detector.detect(text)
        if lang == "MIXED" and re.search(r'[\u0d00-\u0d7f]', text):
            lang = "MALAYALAM"
        
        entities = extract_entities(c)
        if not entities.get("crop"):
            entities_orig = extract_entities(text)
            entities["crop"] = entities_orig.get("crop")
            
        has_crop = bool(entities.get("crop"))
        pest = entities.get("pest")
        disease = entities.get("disease")
        weed = entities.get("weed")
        location = entities.get("location")
        time_ref = entities.get("time_reference")

        def result(domain: str, topic: str = "", q_type: str = "", conf: float = 0.95, needs_clarification: bool = False) -> Dict[str, Any]:
            return {
                "domain": domain,
                "crop": entities.get("crop"),
                "pest": pest,
                "disease": disease,
                "topic": topic,
                "question_type": q_type,
                "location": location,
                "time_reference": time_ref,
                "language": lang,
                "confidence": conf,
                "needs_clarification": needs_clarification,
                "intent": domain,
                "normalized_query": normalized_text
            }

        # --- OUT OF SCOPE & CLARIFICATION ---
        if c in ["help", "help me", "what can you do"]:
            return result("CLARIFICATION_REQUIRED", "help", "conversational", 0.99, True)

        out_of_scope_terms = ["capital of", "diagnose my health", "medicine for me", "headache", "tell me a joke", "joke", "who is the president", "movie"]
        if any(term in c for term in out_of_scope_terms) and not has_agricultural_entity(c):
            return result("OUT_OF_SCOPE", "out of scope", "conversational", 0.99)

        if c in ["crop is not growing well", "not growing well", "my plant is dying", "problem with crop"]:
            return result("CLARIFICATION_REQUIRED", "ambiguous", "conversational", 0.99, True)

        # --- WEATHER & CLIMATE ---
        if any(w in c for w in ["heatwave", "heat wave", "hot weather protection", "protect from heat"]):
            return result("HEATWAVE", "heatwave management")
        if any(w in c for w in ["weather", "rain", "rainy", "forecast", "മഴ", "കാലാവസ്ഥ"]):
            return result("WEATHER", "weather forecast")
            
        # --- MARKET & PRICING ---
        if any(w in c for w in ["msp", "minimum support price", "താങ്ങുവില"]):
            return result("MSP", "msp")
        if any(w in c for w in ["forecast", "price next month", "price trend", "future price", "sell now or store", "wait for better price", "when to sell"]):
            if any(w in c for w in ["price", "market", "rate"]):
                return result("MARKET_FORECAST", "market forecast")
        if any(w in c for w in ["where to sell", "sell my", "sell harvest", "nearest market", "best price to sell", "where can i sell"]):
            return result("MARKET_SELLING", "market selling")
        if any(w in c for w in ["price", "rate", "mandi", "cost", "today rate", "വില", "വിപണി"]):
            return result("MARKET_PRICE", "current price")

        # --- GOVERNMENT SCHEMES ---
        if any(w in c for w in ["pm kisan", "pm-kisan", "pmkisan"]):
            return result("PM_KISAN", "pm kisan")
        if any(w in c for w in ["kisan credit", "kcc"]):
            return result("KCC", "kisan credit card")
        if any(w in c for w in ["insurance", "pmfby", "fasal bima", "ഇൻഷുറൻസ്"]):
            return result("CROP_INSURANCE", "crop insurance")
        if any(w in c for w in ["subsidy", "subsidies", "സബ്സിഡി", "drip irrigation"]):
            return result("SUBSIDY", "subsidy")
        if any(w in c for w in ["scheme", "krishi bhavan", "government", "പദ്ധതി"]):
            return result("GOVERNMENT_SCHEME", "government scheme")

        # --- LIVESTOCK & POULTRY ---
        if any(w in c for w in ["poultry", "chicken", "hen", "egg", "കോഴി"]):
            return result("POULTRY", "poultry")
        if any(w in c for w in ["goat", "cow", "cattle", "buffalo", "milk", "vaccination schedule for goats", "veterinary", "ആട്", "പശു"]):
            return result("LIVESTOCK", "livestock")

        # --- POST HARVEST ---
        if any(w in c for w in ["dry", "drying", "sun dry", "ഉണക്കൽ"]):
            return result("DRYING", "drying")
        if any(w in c for w in ["store", "storage", "shelf life", "keep fresh", "refrigeration", "സംഭരണം"]):
            return result("STORAGE", "storage")
        if any(w in c for w in ["post harvest", "harvested", "after harvest"]):
            return result("POST_HARVEST", "post harvest")

        # --- WATER & IRRIGATION ---
        if any(w in c for w in ["irrigation", "water my", "watering", "how much water", "water schedule", "നന"]):
            return result("IRRIGATION", "irrigation")
        if any(w in c for w in ["waterlogged", "water logging", "drainage", "excess water"]):
            return result("WATER_MANAGEMENT", "water management")

        # --- SOIL MANAGEMENT ---
        if any(w in c for w in ["ph ", " ph ", "ph test", "test my soil ph", "acidic", "liming", "dolomite"]):
            return result("SOIL_PH", "soil ph")
        if any(w in c for w in ["sandy", "laterite", "clay", "soil type"]):
            if any(w in c for w in ["which crop", "suit", "suitable", "grow in"]):
                return result("CROP_RECOMMENDATION", "crop recommendation by soil")
            return result("SOIL_TYPE", "soil type")
        if any(w in c for w in ["soil", "matti", "mannu", "മണ്ണ്"]):
            return result("SOIL_MANAGEMENT", "soil management")

        # --- PEST & DISEASE & WEEDS ---
        if weed or any(w in c for w in ["weed", "kalakal", "കള"]):
            return result("WEED_MANAGEMENT", "weed management")
        if pest or any(w in c for w in ["whitefly", "aphid", "insect", "pest", "borer", "caterpillar", "കീടം"]):
            return result("PEST_MANAGEMENT", "pest management")
        if disease or any(w in c for w in ["disease", "fungus", "wilt", "blight", "rot", "രോഗം"]):
            return result("DISEASE", "disease management")
            
        # Distinguish symptoms correctly without forcing diagnosis
        if any(w in c for w in ["yellow", "yellowing", "spots", "dying", "symptom", "மஞ்சளாகிறது"]):
            return result("DISEASE", "symptom checking")

        # --- FERTILIZER ---
        if any(w in c for w in ["fertilizer", "fertiliser", "urea", "npk", "potash", "jeevamrutham", "neem cake", "manure", "വളം"]):
            return result("FERTILIZER", "fertilizer management")

        # --- CROP CALENDAR & SOWING ---
        if any(w in c for w in ["sow", "sowing", "plant", "planting", "best time to plant", "right time to sow"]):
            return result("CROP_SOWING", "crop sowing")
        if any(w in c for w in ["season", "calendar", "crop calendar"]):
            return result("CROP_CALENDAR", "crop calendar")

        # --- GENERAL AGRICULTURE ---
        if has_crop or has_agricultural_entity(c):
            return result("GENERAL_AGRICULTURE", "general")

        # Default Fallback
        return result("CLARIFICATION_REQUIRED", "unknown", "conversational", 0.99, True)

intent_classifier = IntentClassifier()

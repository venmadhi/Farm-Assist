import re
import logging
from typing import Dict, Any, Optional
from ..config import settings
from .gemini_agent import gemini_agent

logger = logging.getLogger(__name__)

class ResponseGenerator:
    @staticmethod
    def _context_field(kb_context: str, field_name: str) -> str:
        prefix = f"{field_name}:"
        for line in kb_context.splitlines():
            if line.startswith(prefix):
                return line[len(prefix):].strip()
        return ""

    @staticmethod
    def _verified_context(kb_context: str, intent: str, query: str, crop_entity: Optional[str] = None) -> str:
        """Filter retrieved context to keep only reference blocks strictly relevant to both crop and intent."""
        if not kb_context:
            return ""

        blocks = re.split(r"\n\s*\n", kb_context.strip())
        verified = []

        for block in blocks:
            document_crop = ResponseGenerator._context_field(block, "Crop").lower()
            document_title = ResponseGenerator._context_field(block, "Document Title").lower()
            document_intent = ResponseGenerator._context_field(block, "Intent").upper()
            content_lower = block.lower()

            # 1. Crop relevance check
            crop_matches = True
            if crop_entity:
                target_crop = crop_entity.lower()
                crop_alias_targets = ["rice", "paddy", "nellu"] if target_crop in ["rice", "paddy", "nellu"] else [target_crop]
                
                if document_crop and document_crop != "general":
                    crop_matches = any(alias in document_crop for alias in crop_alias_targets) or any(alias in document_title for alias in crop_alias_targets)
                elif document_crop == "general":
                    if intent in ["FERTILIZER_RECOMMENDATION", "MANURE_RECOMMENDATION", "CROP_SUITABILITY", "CROP_SELECTION", "POST_HARVEST"]:
                        crop_matches = any(alias in content_lower for alias in crop_alias_targets)
                    else:
                        crop_matches = True
            else:
                crop_matches = (document_crop == "general" or not document_crop)

            # 2. Intent relevance check
            intent_matches = False
            
            intent_mapping = {
                "WEATHER": ["WEATHER", "CLIMATE"],
                "HEATWAVE": ["WEATHER", "CLIMATE"],
                "CROP_CALENDAR": ["CROP_CULTIVATION", "SOWING", "PLANTING"],
                "CROP_SOWING": ["CROP_CULTIVATION", "SOWING", "PLANTING"],
                "CROP_RECOMMENDATION": ["CROP_SUITABILITY", "CROP_SELECTION"],
                "PEST_MANAGEMENT": ["PEST"],
                "WEED_MANAGEMENT": ["WEED"],
                "DISEASE": ["DISEASE", "PATHOGEN"],
                "SOIL_MANAGEMENT": ["SOIL_WATER", "SOIL_TEST"],
                "SOIL_TYPE": ["SOIL_WATER", "CROP_SUITABILITY"],
                "SOIL_PH": ["SOIL_PH"],
                "WATER_MANAGEMENT": ["WATER", "DRAINAGE", "SOIL_WATER"],
                "IRRIGATION": ["IRRIGATION", "WATER"],
                "FERTILIZER": ["FERTILIZER", "NUTRIENT", "MANURE", "ORGANIC_FARMING"],
                "MARKET_PRICE": ["MARKET", "PRICE"],
                "MARKET_SELLING": ["MARKET", "PRICE"],
                "MARKET_FORECAST": ["MARKET", "PRICE"],
                "MSP": ["MSP", "PRICE"],
                "GOVERNMENT_SCHEME": ["GOVERNMENT", "SCHEME"],
                "SUBSIDY": ["SUBSIDY", "SCHEME"],
                "PM_KISAN": ["PM_KISAN", "SCHEME"],
                "CROP_INSURANCE": ["INSURANCE"],
                "KCC": ["GOVERNMENT", "SCHEME"],
                "POST_HARVEST": ["POST_HARVEST"],
                "STORAGE": ["STORAGE", "POST_HARVEST"],
                "DRYING": ["DRYING", "POST_HARVEST"],
                "LIVESTOCK": ["LIVESTOCK", "ANIMAL"],
                "POULTRY": ["POULTRY", "LIVESTOCK"],
                "GENERAL_AGRICULTURE": ["GENERAL", "FARMING"]
            }
            
            if intent in intent_mapping:
                expected_intents = intent_mapping[intent]
                if any(exp == document_intent or document_intent.startswith(exp + "_") for exp in expected_intents):
                    intent_matches = True
            
            if not intent_matches:
                if intent == "FERTILIZER":
                    if "fertilizer" in document_title or "nutrient" in document_title or "വളം" in block or "jeevamrutham" in content_lower:
                        intent_matches = True
                elif intent == "WEED_MANAGEMENT":
                    intent_matches = any(term in content_lower for term in ["weed", "weeds", "kalakal", "കള"])
                elif intent in ["SOIL_MANAGEMENT", "SOIL_TYPE", "SOIL_PH", "WATER_MANAGEMENT", "IRRIGATION"]:
                    intent_matches = any(term in content_lower for term in ["soil", "texture", "ph", "drainage", "water", "clay", "acidity", "irrigation", "laterite", "sandy"])
                elif intent in ["CROP_RECOMMENDATION", "CROP_SOWING", "CROP_CALENDAR"]:
                    intent_matches = any(term in content_lower for term in ["suitability", "climate", "crop selection", "recommendation", "cultivation", "temperature", "planting", "sowing", "jeevamrutham", "organic"])
                elif intent in ["POST_HARVEST", "STORAGE", "DRYING"]:
                    intent_matches = any(term in content_lower for term in ["harvest", "post-harvest", "drying", "storage", "grain", "spoilage", "mold"])
                elif intent == "PEST_MANAGEMENT":
                    intent_matches = any(term in content_lower for term in ["pest", "beetle", "borer", "weevil", "aphid", "chellu", "whitefly", "whiteflies", "insect"])
                elif intent == "DISEASE":
                    intent_matches = any(term in content_lower for term in ["disease", "wilt", "rot", "sigatoka", "blight", "fungicide", "fungus", "bacteria", "virus"])
                elif intent in ["WEATHER", "HEATWAVE"]:
                    intent_matches = any(term in content_lower for term in ["weather", "rain", "monsoon", "climate", "temperature", "heatwave", "drought"])
                elif intent in ["MARKET_PRICE", "MARKET_SELLING", "MARKET_FORECAST", "MSP"]:
                    intent_matches = any(term in content_lower for term in ["price", "market", "sell", "mandi", "msp", "rate"])
                elif intent in ["GOVERNMENT_SCHEME", "SUBSIDY", "PM_KISAN", "CROP_INSURANCE", "KCC"]:
                    intent_matches = any(term in content_lower for term in ["scheme", "subsidy", "insurance", "loan", "credit", "kisan"])
                elif intent in ["LIVESTOCK", "POULTRY"]:
                    intent_matches = any(term in content_lower for term in ["livestock", "goat", "cow", "poultry", "hen", "cattle", "milk", "feed", "vaccination"])
                else:
                    intent_matches = True

            if intent == "FERTILIZER" and "jeevamrutham" in document_title and crop_entity and "jeevamrutham" not in query.lower():
                intent_matches = False

            if crop_matches and intent_matches:
                verified.append(block)

        return verified[0] if verified else ""

    def generate_response(self, rag_data: Dict[str, Any], api_key: str = None, image_data: Optional[str] = None) -> str:
        """Generates grounded response using Gemini."""
        intent = rag_data["intent"]
        original_query = rag_data["original_query"]
        kb_context = rag_data["kb_context"]
        crop_entity = rag_data.get("crop_entity")
        
        # Strictly verify KB context for the specific crop and intent
        rag_data["kb_context"] = self._verified_context(kb_context, intent, original_query, crop_entity)

        # Delegate response generation entirely to Gemini
        gemini_api_key = api_key or settings.GEMINI_API_KEY
        return gemini_agent.generate_response(rag_data, gemini_api_key, image_data)

    def generate_response_stream(self, rag_data: Dict[str, Any], api_key: str = None, image_data: Optional[str] = None):
        """Generates grounded response using Gemini (Streaming)."""
        intent = rag_data["intent"]
        original_query = rag_data["original_query"]
        kb_context = rag_data["kb_context"]
        crop_entity = rag_data.get("crop_entity")
        
        # Strictly verify KB context for the specific crop and intent
        rag_data["kb_context"] = self._verified_context(kb_context, intent, original_query, crop_entity)

        # Delegate response generation entirely to Gemini
        gemini_api_key = api_key or settings.GEMINI_API_KEY
        return gemini_agent.generate_response_stream(rag_data, gemini_api_key, image_data)

response_generator = ResponseGenerator()

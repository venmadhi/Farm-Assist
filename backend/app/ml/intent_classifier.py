import os
import pickle
import numpy as np
from typing import Dict, Any
from .thanglish_normalizer import thanglish_normalizer

class IntentClassifier:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.classes = [
            'CROP_RECOMMENDATION',
            'FERTILIZER',
            'DISEASE',
            'SOIL',
            'WEATHER',
            'IRRIGATION',
            'ORGANIC_FARMING',
            'MARKET',
            'PROFIT',
            'CULTIVATION',
            'GOVERNMENT_SCHEME',
            'AGRICULTURAL_QUERY',
            'GREETING',
            'CASUAL_CONVERSATION',
            'CONFIRMATION',
            'THANKS',
            'GOODBYE',
            'UNKNOWN'
        ]
        self.load_model()
        
    def load_model(self):
        ml_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.abspath(os.path.join(ml_dir, "..", "models", "intent_model", "intent_model.pkl"))
        
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data.get('model')
                    self.vectorizer = data.get('vectorizer')
                    # Sync classes if available
                    if 'classes' in data:
                        self.classes = data['classes']
                print("Intent Classifier model loaded successfully.")
            except Exception as e:
                print(f"Error loading intent classifier model: {e}")
        else:
            print("Intent Classifier model not found. Fallback to rule-based classification.")

    def predict(self, text: str) -> Dict[str, Any]:
        normalized_text = thanglish_normalizer.normalize(text)
        c = normalized_text.lower().strip()
        
        # --- 1. CONVERSATIONAL OVERRIDES (Must bypass RAG) ---
        
        # GREETING
        greetings = ["hi", "hii", "hello", "hey", "namaskaram", "hai", "good morning", "good afternoon", "good evening"]
        if any(c == g or c.startswith(g + " ") for g in greetings):
            return {"intent": "GREETING", "confidence": 0.99, "normalized_query": normalized_text}
            
        # GOODBYE
        goodbyes = ["bye", "goodbye", "povaanu", "see you", "see u", "tc", "take care"]
        if any(c == gb or c.startswith(gb + " ") for gb in goodbyes):
            return {"intent": "GOODBYE", "confidence": 0.99, "normalized_query": normalized_text}
            
        # THANKS
        thanks = ["thank you", "thanks", "nanni", "chinthamanu", "thx", "thank you so much"]
        if any(t in c for t in thanks):
            return {"intent": "THANKS", "confidence": 0.99, "normalized_query": normalized_text}
            
        # CONFIRMATION
        confirmations = ["manasilayo", "ok", "okay", "understood", "yes", "no", "sherikkum", "correct", "true", "understood", "fine"]
        if any(c == conf or c.startswith(conf + " ") for conf in confirmations):
            return {"intent": "CONFIRMATION", "confidence": 0.99, "normalized_query": normalized_text}
            
        # CASUAL_CONVERSATION
        casuals = ["how are you", "sugamano", "enthundu vishesham", "who are you", "what can you do", "parayu", "details"]
        if any(cas in c for cas in casuals):
            return {"intent": "CASUAL_CONVERSATION", "confidence": 0.98, "normalized_query": normalized_text}

        # --- 2. EXPLICIT AGRICULTURAL SUB-INTENTS (High Precision) ---
        
        # Crop Suitability
        if any(kw in c for kw in ["suitable crop", "profitable crop", "plant after", "krishi cheyyam", "crop suitable", "crop recommendation", "recommend crop", "which crop", "what crop", "profitable crop"]):
            return {"intent": "CROP_RECOMMENDATION", "confidence": 0.95, "normalized_query": normalized_text}
            
        # Weather
        if any(kw in c for kw in ["weather", "rain", "mazha", "temperature", "humidity", "climate", "forecast"]):
            return {"intent": "WEATHER", "confidence": 0.95, "normalized_query": normalized_text}
            
        # Market
        if any(kw in c for kw in ["price", "vila", "market", "rate", "cost", "rupees", "inr"]):
            if not any(kw in c for kw in ["crop", "plant"]):
                return {"intent": "MARKET", "confidence": 0.95, "normalized_query": normalized_text}
                
        # Government schemes
        if any(kw in c for kw in ["government scheme", "pm kisan", "crop insurance", "subsidy", "krishi bhavan", "insurance"]):
            return {"intent": "GOVERNMENT_SCHEME", "confidence": 0.95, "normalized_query": normalized_text}

        # Organic farming
        if any(kw in c for kw in ["organic", "jaiva", "jeevamrutham", "neem oil", "garlic", "emulsion", "cow dung"]):
            return {"intent": "ORGANIC_FARMING", "confidence": 0.95, "normalized_query": normalized_text}

        # Fertilizer
        if any(kw in c for kw in ["valam", "fertilizer", "fertiliser", "NPK", "urea", "potash", "dolomite", "lime"]):
            return {"intent": "FERTILIZER", "confidence": 0.95, "normalized_query": normalized_text}
            
        # Soil
        if any(kw in c for kw in ["soil", "mannu", "acidity", "acid", "ph level"]):
            return {"intent": "SOIL", "confidence": 0.95, "normalized_query": normalized_text}

        # Irrigation
        if any(kw in c for kw in ["irrigation", "water", "vellam", "watering", "dryness"]):
            return {"intent": "IRRIGATION", "confidence": 0.95, "normalized_query": normalized_text}

        # Disease/Deficiency
        if any(kw in c for kw in ["disease", "puzhu", "chellu", "vaattam", "wilt", "blight", "sigatoka", "spots", "yellow", "manja", "spot", "pindi", "unni", "decay", "rot", "insect"]):
            if not any(kw in c for kw in ["potassium", "nitrogen", "soil test"]):
                return {"intent": "DISEASE", "confidence": 0.95, "normalized_query": normalized_text}

        # Profit
        if any(kw in c for kw in ["profit", "revenue", "income", "price increase", "profitable"]):
            return {"intent": "PROFIT", "confidence": 0.95, "normalized_query": normalized_text}

        # Cultivation
        if any(kw in c for kw in ["cultivation", "harvest", "grow", "spacing", "planting", "tapping"]):
            return {"intent": "CULTIVATION", "confidence": 0.95, "normalized_query": normalized_text}

        # --- 3. MODEL PREDICTION FOR COMPLEX AGRICULTURAL TEXTS ---
        if self.model and self.vectorizer:
            try:
                X = self.vectorizer.transform([normalized_text])
                probs = self.model.predict_proba(X)[0]
                pred_idx = int(np.argmax(probs))
                intent = self.classes[pred_idx]
                confidence = float(probs[pred_idx])
                
                # Map old model output classes to the requested new ones
                class_mapping = {
                    'CROP_RECOMMENDATION': 'CROP_RECOMMENDATION',
                    'FERTILIZER_RECOMMENDATION': 'FERTILIZER',
                    'DISEASE_OR_DEFICIENCY': 'DISEASE',
                    'MARKET_PRICES': 'MARKET',
                    'GENERAL_ADVISORY': 'AGRICULTURAL_QUERY',
                    'OUT_OF_DOMAIN': 'UNKNOWN'
                }
                
                mapped_intent = class_mapping.get(intent, 'AGRICULTURAL_QUERY')
                return {
                    "intent": mapped_intent,
                    "confidence": round(confidence, 4),
                    "normalized_query": normalized_text
                }
            except Exception as e:
                print(f"Model predict failed: {e}. Falling back to default.")

        # --- 4. GENERAL FALLBACK ---
        if any(kw in c for kw in ["crop", "plant", "grow", "farming", "agriculture", "farmer", "field", "seed"]):
            return {"intent": "AGRICULTURAL_QUERY", "confidence": 0.80, "normalized_query": normalized_text}
            
        return {"intent": "UNKNOWN", "confidence": 0.50, "normalized_query": normalized_text}

intent_classifier = IntentClassifier()

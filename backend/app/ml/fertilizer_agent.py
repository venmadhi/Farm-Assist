import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, List
import shap

class FertilizerAgent:
    def __init__(self):
        self.model_bundle = None
        self.load_model()
        
    def load_model(self):
        ml_dir = os.path.dirname(__file__)
        model_path = os.path.join(ml_dir, 'fertilizer_model.pkl')
        try:
            with open(model_path, 'rb') as f:
                self.model_bundle = pickle.load(f)
            print("ML Fertilizer Recommendation model loaded.")
        except Exception as e:
            print(f"Fertilizer model load error: {e}")

    def _map_soil(self, soil: str) -> str:
        s = soil.lower().strip()
        # Dataset Soil Types: ['Sandy' 'Loamy' 'Black' 'Red' 'Clayey']
        if 'sandy' in s:
            return 'Sandy'
        elif 'clay' in s:
            return 'Clayey'
        elif 'black' in s:
            return 'Black'
        elif 'laterite' in s or 'red' in s:
            return 'Red'
        else:
            return 'Loamy' # Default fallback

    def _map_crop(self, crop: str) -> str:
        c = crop.lower().strip()
        # Dataset Crop Types: ['Maize' 'Sugarcane' 'Cotton' 'Tobacco' 'Paddy' 'Barley' 'Wheat' 'Millets' 'Oil seeds' 'Pulses' 'Ground Nuts']
        if c in ['rice', 'paddy']:
            return 'Paddy'
        elif c == 'maize':
            return 'Maize'
        elif c == 'coconut':
            return 'Oil seeds'
        elif c in ['lentil', 'blackgram', 'mungbean', 'chickpea', 'pigeonpeas', 'mothbeans']:
            return 'Pulses'
        elif c in ['coffee', 'tea', 'cardamom', 'pepper']:
            return 'Tobacco' # Plantation crop proxy
        else:
            return 'Paddy' # Safe default mapping

    def calculate_fertilizer(
        self, crop: str, n: float, p: float, k: float, ph: float, 
        soil_type: str = "Laterite", temperature: float = None, humidity: float = None
    ) -> Dict[str, Any]:
        crop = crop.lower().strip()
        
        # 1. STRICT WEATHER VALIDATION - No Mocking/Fabrication
        if temperature is None or humidity is None:
            raise ValueError("Recent temperature and humidity data are required to run the fertilizer recommendation model.")
            
        if self.model_bundle is None:
            raise RuntimeError("Fertilizer recommendation model is not initialized/loaded.")
            
        model = self.model_bundle['model']
        feature_names = self.model_bundle['feature_names']
        encoders = self.model_bundle['encoders']
        
        # Encode parameters
        crop_mapped = self._map_crop(crop)
        soil_mapped = self._map_soil(soil_type)
        
        crop_encoded = encoders['crop_type'].transform([crop_mapped])[0]
        soil_encoded = encoders['soil_type'].transform([soil_mapped])[0]
        
        # Estimate soil moisture from humidity to feed the model
        moisture = float(np.clip(humidity * 0.7 - (temperature - 25.0) * 1.5, 10.0, 95.0))
        
        input_data = {
            'temperature': temperature,
            'humidity': humidity,
            'moisture': moisture,
            'soil_type': soil_encoded,
            'crop_type': crop_encoded,
            'nitrogen': n,
            'potassium': k,
            'phosphorus': p
        }
        
        df_input = pd.DataFrame([input_data])[feature_names]
        
        # 2. ML INFERENCE
        pred_idx = model.predict(df_input)[0]
        recommended_fertilizer = encoders['fertilizer'].inverse_transform([pred_idx])[0]
        
        # Compute confidence probability
        confidence = 1.0
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(df_input)[0]
            confidence = float(probs[pred_idx])
            
        # 3. SHAP EXPLAINABILITY
        shap_explanation = {}
        top_factors = []
        try:
            background = self.model_bundle.get('X_train_sample')
            if background is not None:
                explainer = shap.Explainer(model, background)
                shap_vals = explainer(df_input)
                vals = shap_vals.values
                
                # Handle SHAP dimensionality
                if len(vals.shape) == 3: # Multi-class classifier output
                    feature_shaps = vals[0, :, pred_idx]
                elif len(vals.shape) == 2:
                    feature_shaps = vals[0, :]
                else:
                    feature_shaps = vals.flatten()
                    
                for idx, feat in enumerate(feature_names):
                    shap_explanation[feat] = float(feature_shaps[idx])
                
                # Extract top factors sorted by absolute SHAP impact
                sorted_shaps = sorted(shap_explanation.items(), key=lambda x: abs(x[1]), reverse=True)
                top_factors = [item[0] for item in sorted_shaps[:2]]
        except Exception as e:
            print(f"SHAP explanation calculation failed: {e}")
            
        # 4. AGRONOMIC SCHEDULING & SAFE ORGANIC LAYER
        CROP_THRESHOLDS = {
            "paddy": {"n": 60, "p": 35, "k": 30, "ph_min": 5.5, "ph_max": 6.5},
            "coconut": {"n": 40, "p": 20, "k": 80, "ph_min": 5.5, "ph_max": 7.0},
            "banana": {"n": 80, "p": 40, "k": 100, "ph_min": 6.0, "ph_max": 7.5},
            "pepper": {"n": 45, "p": 30, "k": 50, "ph_min": 5.5, "ph_max": 6.5},
            "rubber": {"n": 30, "p": 15, "k": 35, "ph_min": 4.5, "ph_max": 5.5},
            "cardamom": {"n": 50, "p": 30, "k": 60, "ph_min": 5.0, "ph_max": 6.5},
            "default": {"n": 50, "p": 30, "k": 50, "ph_min": 5.5, "ph_max": 7.0},
        }
        
        req = CROP_THRESHOLDS.get(crop, CROP_THRESHOLDS["default"])
        
        n_status = "Optimal" if n >= req["n"] else "Deficient"
        p_status = "Optimal" if p >= req["p"] else "Deficient"
        k_status = "Optimal" if k >= req["k"] else "Deficient"
        
        # Override ML prediction if logically inconsistent with agronomic reality
        zero_k_fertilizers = ["Urea", "DAP", "28-28", "20-20"]
        zero_p_fertilizers = ["Urea"]
        
        if k_status == "Deficient" and recommended_fertilizer in zero_k_fertilizers:
            recommended_fertilizer += " + Muriate of Potash (MOP)"
        elif p_status == "Deficient" and recommended_fertilizer in zero_p_fertilizers:
            recommended_fertilizer += " + Super Phosphate"
        
        # Calculate dosage based on agronomic deficits
        deficit = max(0, 150.0 - (n + p + k))
        dosage = round(30.0 + (deficit * 0.2), 1)
        
        schedule = [
            {
                "stage": "Basal / Planting Stage (Day 0)",
                "fertilizer_name": "Well-rotted Farmyard Manure (FYM)",
                "amount_grams_per_sqm": 500.0,
                "organic_alternatives": ["Compost (250g/sqm)", "Coir Pith Compost"]
            },
            {
                "stage": "Vegetative Growth (Day 30-45)",
                "fertilizer_name": recommended_fertilizer,
                "amount_grams_per_sqm": round(dosage * 0.6, 1),
                "organic_alternatives": ["Neem cake mixed compost", "Fish Amino Acid spray (5ml/L)"]
            },
            {
                "stage": "Flowering & Yield (Day 75-90)",
                "fertilizer_name": "Potash split / Organic Ash",
                "amount_grams_per_sqm": round(dosage * 0.4, 1),
                "organic_alternatives": ["Wood Ash (potassium rich)", "Coconut Husk Ash"]
            }
        ]
        
        tips = []
        if ph < req["ph_min"]:
            tips.append(f"Soil pH ({ph:.1f}) is highly acidic. Apply agricultural Lime or Dolomite at 150g/sqm to boost availability of phosphorus.")
        elif ph > req["ph_max"]:
            tips.append(f"Soil pH ({ph:.1f}) is alkaline. Apply organic gypsum to balance soil pH.")
            
        if n_status == "Deficient":
            tips.append("Incorporate cover cropping (leguminous cowpeas or mucuna) in off-season to capture natural atmospheric Nitrogen.")
        if k_status == "Deficient" and crop == "coconut":
            tips.append("Bury coconut husks in trenches around palm root basins. Decomposing husks release organic potassium slow-release fertilizers.")

        cost_multiplier = 0.8 if "Organic" in recommended_fertilizer else 1.5 if "NPK" in recommended_fertilizer else 1.1
        estimated_cost = round(dosage * cost_multiplier * 0.35 * 10, 2)
        
        # Formulate explanation sentence
        factors_str = " and ".join(top_factors) if top_factors else "NPK nutrient profile"
        explanation = f"Based on your soil's {factors_str}, the model predicted a recommendation of {recommended_fertilizer} (Confidence: {confidence * 100:.1f}%)."

        return {
            "crop_name": crop.capitalize(),
            "n_status": n_status,
            "p_status": p_status,
            "k_status": k_status,
            "fertilizer_schedule": schedule,
            "sustainability_tips": tips,
            "estimated_cost": estimated_cost,
            "confidence_score": confidence,
            "model_version": "ML-Classifier-v1.0",
            "explanation": explanation,
            "shap_explanation": shap_explanation
        }

fertilizer_agent = FertilizerAgent()

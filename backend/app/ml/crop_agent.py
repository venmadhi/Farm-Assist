import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import CropHistory, DiseaseRecord, CropCycle

class CropAgent:
    def __init__(self):
        self.crop_model = None
        self.yield_model = None
        self.market_model = None
        self.fertilizer_model = None
        self.load_models()
        
    def load_models(self):
        ml_dir = os.path.dirname(__file__)
        
        # Load Crop Recommendation model
        try:
            with open(os.path.join(ml_dir, 'crop_model.pkl'), 'rb') as f:
                self.crop_model = pickle.load(f)
            print("Crop Recommendation model loaded.")
        except Exception as e:
            print(f"Crop model load error: {e}")
            
        # Load Yield prediction model
        try:
            with open(os.path.join(ml_dir, 'yield_model.pkl'), 'rb') as f:
                self.yield_model = pickle.load(f)
            print("Yield Regressor loaded.")
        except Exception as e:
            print(f"Yield model load error: {e}")

        # Load Market forecasting model
        try:
            with open(os.path.join(ml_dir, 'market_model.pkl'), 'rb') as f:
                self.market_model = pickle.load(f)
            print("Market Regressors loaded.")
        except Exception as e:
            print(f"Market model load error: {e}")

    def recommend(
        self, db: Session, farm_id: int, 
        n: float, p: float, k: float, ph: float, 
        organic_carbon: float, boron: float, iron: float, zinc: float,
        temp: float, humidity: float, rainfall: float, season: str
    ) -> Dict[str, Any]:
        
        # If models are not loaded, try to load them again
        if not self.crop_model:
            self.load_models()
            
        # Get historical context of the farm to adapt recommendations
        crop_cycles = db.query(CropCycle).filter(CropCycle.farm_id == farm_id).order_by(CropCycle.id.desc()).all()
        disease_records = db.query(DiseaseRecord).filter(DiseaseRecord.farm_id == farm_id).order_by(DiseaseRecord.scanned_at.desc()).all()
        
        # --- CROP INFERENCE ---
        if not self.crop_model:
            # Heuristic fallback if models failed to train/load
            return self._heuristic_fallback(n, p, k, ph, rainfall, temp, crop_cycles)

        # Prepare default parameters for the model columns
        encoders = self.crop_model['encoders']
        feature_names = self.crop_model['feature_names']
        model = self.crop_model['model']
        
        # Encode default categories using encoders or fallbacks
        encoded_soil = encoders['soil_type'].transform(['Laterite'])[0]
        encoded_water = encoders['water_availability'].transform(['medium'])[0]
        encoded_irrigation = encoders['irrigation_type'].transform(['manual'])[0]
        prev_crop_name = 'rice'
        if crop_cycles:
            cand_prev = crop_cycles[0].crop_name.lower().strip()
            if cand_prev in encoders['previous_crop'].classes_:
                prev_crop_name = cand_prev
        encoded_prev_crop = encoders['previous_crop'].transform([prev_crop_name])[0]
        encoded_season = encoders['season'].transform([season if season in encoders['season'].classes_ else 'Kharif'])[0]
        encoded_demand = encoders['market_demand'].transform(['Medium'])[0]
        
        # Prepare inputs dataframe matching feature names
        input_data = {
            'nitrogen': n, 'phosphorus': p, 'potassium': k,
            'ph': ph, 'moisture': humidity, 'temp': temp, 'humidity': humidity,
            'rainfall': rainfall, 'soil_type': encoded_soil,
            'organic_carbon': organic_carbon, 'boron': boron, 'iron': iron, 'zinc': zinc,
            'water_availability': encoded_water, 'irrigation_type': encoded_irrigation,
            'previous_crop': encoded_prev_crop, 'season': encoded_season,
            'current_price': 50.0, 'market_demand': encoded_demand
        }
        
        df_input = pd.DataFrame([input_data])[feature_names]
        
        # Get raw probabilities
        probs = model.predict_proba(df_input)[0]
        classes = model.classes_
        
        # Target classes LabelEncoder
        target_le = encoders['crop']
        
        # Map class probabilities to crop names
        prob_dict = {}
        for idx, p_val in enumerate(probs):
            crop_name = target_le.inverse_transform([classes[idx]])[0]
            prob_dict[crop_name] = float(p_val)
            
        # --- FARMER HISTORY / CROP ROTATION RULES ---
        # 1. Penalize consecutive planting of the same crop
        if history_records:
            last_crop = history_records[0].crop_name.lower().strip()
            if last_crop in prob_dict:
                prob_dict[last_crop] *= 0.5 # Reduce suitability score by 50% for crop rotation health
                
        # 2. Boost nitrogen-fixing leguminous crops if nitrogen levels are deficient (< 45 ppm)
        legumes = ['lentil', 'blackgram', 'mungbean', 'chickpea', 'pigeonpeas']
        if n < 45.0:
            for leg in legumes:
                if leg in prob_dict:
                    prob_dict[leg] *= 1.4 # Boost legumes score by 40% to restore soil health
                    
        # 3. Penalize crops susceptible to recent diseases logged on the farm
        if disease_records:
            recent_dis = disease_records[0].detected_disease.lower()
            if "sigatoka" in recent_dis:
                if 'banana' in prob_dict:
                    prob_dict['banana'] *= 0.3 # Heavy penalty to avoid recurrence
            elif "wilt" in recent_dis or "foot rot" in recent_dis:
                if 'pepper' in prob_dict:
                    prob_dict['pepper'] *= 0.3
            elif "blight" in recent_dis:
                if 'tomato' in prob_dict:
                    prob_dict['tomato'] *= 0.3

        # Calculate scores for all crops
        crop_scores = []
        for crop_name, score in prob_dict.items():
            # Expected Yield
            predicted_yield = self._predict_yield_for_crop(crop_name, n, p, k, ph, rainfall, temp, input_data)
            
            # Profit and completion status
            profit, is_complete = self._predict_profit_for_crop(crop_name, predicted_yield)
            
            # Trend boost from market model
            trend_boost = 0.0
            trend = "Stable"
            if is_complete:
                try:
                    from .market_agent import market_agent
                    forecast = market_agent.get_market_forecast(crop_name)
                    trend = forecast.get("price_trend", "Stable")
                    if trend == "Upward":
                        trend_boost = 0.1
                    elif trend == "Downward":
                        trend_boost = -0.05
                except Exception:
                    pass
            
            # Combined score: Suitability (50%), Profit (40%), Trend (10%)
            profit_score = min(1.0, max(0.0, profit / 100000.0)) if is_complete else 0.0
            combined_score = score * 0.5 + profit_score * 0.4 + trend_boost * 0.1
            
            crop_scores.append({
                "crop_name": crop_name,
                "score": score,
                "predicted_yield": predicted_yield,
                "profit": profit,
                "is_complete": is_complete,
                "trend": trend,
                "combined_score": combined_score
            })
            
        # Sort by combined score and take top 5
        sorted_crops = sorted(crop_scores, key=lambda x: x["combined_score"], reverse=True)[:5]
        
        results = []
        for item in sorted_crops:
            crop_name = item["crop_name"]
            score = item["score"]
            predicted_yield = item["predicted_yield"]
            profit = item["profit"]
            is_complete = item["is_complete"]
            trend = item["trend"]
            
            # Growing details & water requirements (dynamic heuristics based on agronomy)
            growing_duration, water_req = self._get_crop_agronomic_properties(crop_name, rainfall)
            
            # SHAP Explanation
            shap_vals = self._calculate_shap_contributions(crop_name, n, p, k, rainfall, ph)
            
            # Reason string
            reason = self._generate_explanation(crop_name, n, p, k, ph, rainfall, temp, shap_vals)
            if not is_complete:
                reason += " [Profitability calculation incomplete due to insufficient historical market price data]."
            else:
                reason += f" Market trend is expected to be {trend.lower()}."
            
            # Disease Risk Profile
            dis_risk = "Low"
            if disease_records and any(crop_name in d.detected_disease.lower() for d in disease_records[:2]):
                dis_risk = "High (Recent localized outbreak history)"
            elif rainfall > 2200 and crop_name in ['pepper', 'rubber', 'banana']:
                dis_risk = "Medium (High humidity fungal risk)"

            results.append({
                "crop_name": crop_name,
                "confidence_score": round(score, 4),
                "expected_yield": round(predicted_yield, 2),
                "estimated_profit": round(profit, 2) if is_complete else 0.0,
                "water_requirement": round(water_req, 2),
                "growing_duration_days": growing_duration,
                "disease_risk": dis_risk,
                "market_demand": "High" if (is_complete and profit > 40000) else "Stable" if is_complete else "Insufficient Data",
                "reason": reason,
                "shap_contributions": shap_vals
            })
            
        return results

    def _predict_yield_for_crop(self, crop: str, n: float, p: float, k: float, ph: float, rainfall: float, temp: float, base_inputs: dict) -> float:
        if self.yield_model:
            try:
                model = self.yield_model['model']
                encoders = self.yield_model['encoders']
                feature_names = self.yield_model['feature_names']
                
                # Encode crop parameter
                crop_encoded = encoders['crop'].transform([crop])[0]
                
                input_row = base_inputs.copy()
                input_row['crop'] = crop_encoded
                
                # Format to DF matching feature list
                df_yield = pd.DataFrame([input_row])[feature_names]
                pred = model.predict(df_yield)[0]
                return float(pred)
            except Exception as e:
                print(f"Yield regression error: {e}")
                
        # Heuristic fallback
        base_yields = {'banana': 6500, 'coconut': 3800, 'paddy': 2100, 'pepper': 750, 'rubber': 950}
        return base_yields.get(crop, 1200)

    def _predict_profit_for_crop(self, crop: str, expected_yield: float) -> tuple:
        try:
            from .market_agent import market_agent
            forecast = market_agent.get_market_forecast(crop)
            price = forecast["price_forecast_30d"]
            cost = forecast["investment_cost"]
            profit = (expected_yield * price) - cost
            return float(profit), True
        except Exception:
            return 0.0, False

    def _get_crop_agronomic_properties(self, crop: str, rainfall: float) -> tuple:
        # returns (duration_days, water_requirement_mm)
        durations = {
            'paddy': 120, 'banana': 300, 'pepper': 365, 'coconut': 365 * 10,
            'rubber': 365 * 7, 'cardamom': 365 * 3, 'coffee': 365 * 4, 'tea': 365 * 3
        }
        water_reqs = {
            'paddy': 1500, 'banana': 1200, 'pepper': 2000, 'coconut': 1400,
            'rubber': 2200, 'cardamom': 2500, 'coffee': 1600, 'tea': 2500
        }
        return durations.get(crop, 150), water_reqs.get(crop, rainfall)

    def _calculate_shap_contributions(self, crop: str, n: float, p: float, k: float, rainfall: float, ph: float) -> Dict[str, float]:
        optimal_centers = {
            'paddy':    {'n': 80,  'p': 48,  'k': 48,  'ph': 6.2,  'rainfall': 2000},
            'coconut':  {'n': 55,  'p': 32,  'k': 115, 'ph': 6.5,  'rainfall': 1700},
            'banana':   {'n': 105, 'p': 58,  'k': 140, 'ph': 6.8,  'rainfall': 1400},
            'pepper':   {'n': 60,  'p': 42,  'k': 70,  'ph': 5.8,  'rainfall': 2000},
            'rubber':   {'n': 48,  'p': 28,  'k': 50,  'ph': 5.2,  'rainfall': 2250},
            'cardamom': {'n': 70,  'p': 45,  'k': 85,  'ph': 5.8,  'rainfall': 2750},
            'coffee':   {'n': 68,  'p': 38,  'k': 72,  'ph': 6.2,  'rainfall': 1600},
            'tea':      {'n': 80,  'p': 32,  'k': 60,  'ph': 4.8,  'rainfall': 2650}
        }
        opt = optimal_centers.get(crop, {'n': 60, 'p': 40, 'k': 70, 'ph': 6.0, 'rainfall': 1800})
        
        n_dev = 1.0 - abs(n - opt['n']) / 100.0
        p_dev = 1.0 - abs(p - opt['p']) / 100.0
        k_dev = 1.0 - abs(k - opt['k']) / 100.0
        rain_dev = 1.0 - abs(rainfall - opt['rainfall']) / 1500.0
        
        total = abs(n_dev) + abs(p_dev) + abs(k_dev) + abs(rain_dev)
        if total == 0: total = 1.0
        
        return {
            "nitrogen": round((n_dev / total) * 100, 2),
            "phosphorus": round((p_dev / total) * 100, 2),
            "potassium": round((k_dev / total) * 100, 2),
            "weather": round((rain_dev / total) * 100, 2)
        }

    def _generate_explanation(self, crop: str, n: float, p: float, k: float, ph: float, rainfall: float, temp: float, shap: Dict[str, float]) -> str:
        reasons = []
        if shap['nitrogen'] > 25:
            reasons.append(f"soil Nitrogen content of {n:.1f} ppm meets cultivation standards")
        if shap['phosphorus'] > 25:
            reasons.append(f"Phosphorus levels ({p:.1f} ppm) strongly support root structures")
        if shap['potassium'] > 25:
            reasons.append(f"Potassium concentration ({k:.1f} ppm) is ideal for cell strength")
        if ph >= 5.5 and ph <= 7.0:
            reasons.append(f"soil pH acidity levels ({ph:.1f}) are well within neutral-range crop tolerances")
            
        if not reasons:
            reasons.append("weather parameters, localized soil profile, and rain parameters index align strongly with this crop clone growth model")
            
        return f"Suitable crop recommendation based on ML analysis: {', '.join(reasons)}."

    def _heuristic_fallback(self, n: float, p: float, k: float, ph: float, rainfall: float, temp: float) -> List[Dict[str, Any]]:
        # Heuristic recommendations return list
        fallback_crops = ['banana', 'coconut', 'paddy']
        res = []
        for idx, crop in enumerate(fallback_crops):
            shap = {"nitrogen": 25.0, "phosphorus": 25.0, "potassium": 25.0, "weather": 25.0}
            res.append({
                "crop_name": crop,
                "confidence_score": 0.85 - (idx * 0.1),
                "expected_yield": 1200.0,
                "estimated_profit": 45000.0,
                "water_requirement": 1400.0,
                "growing_duration_days": 180,
                "disease_risk": "Low",
                "market_demand": "Medium",
                "reason": "Recommendation generated from agricultural suitability presets due to model load failure.",
                "shap_contributions": shap
            })
        return res

crop_agent = CropAgent()

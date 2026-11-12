import os
import pickle
import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, List

class MarketAgent:
    def __init__(self):
        self.model_bundle = None
        self.load_model()
        
    def load_model(self):
        ml_dir = os.path.dirname(__file__)
        model_path = os.path.join(ml_dir, 'market_model.pkl')
        try:
            with open(model_path, 'rb') as f:
                self.model_bundle = pickle.load(f)
            print("ML Market forecasting model loaded.")
        except Exception as e:
            print(f"Market model load error: {e}")

    def _map_crop(self, crop: str) -> str:
        c = crop.lower().strip()
        # Supported crops in trained time-series model:
        # ['Paddy-Unhusked', 'Coconut', 'Banana', 'Ginger (Fresh)', 'Turmeric']
        if c in ['rice', 'paddy', 'paddy-uncleaned', 'paddy-unhusked']:
            return 'Paddy-Unhusked'
        elif c == 'coconut':
            return 'Coconut'
        elif c == 'banana':
            return 'Banana'
        elif c == 'ginger':
            return 'Ginger (Fresh)'
        elif c == 'turmeric':
            return 'Turmeric'
        else:
            raise ValueError(f"Insufficient historical market data to forecast prices for crop: '{crop}'.")

    def get_market_forecast(self, crop: str, district: str = "Palakkad", farm_area_acres: float = 1.0) -> Dict[str, Any]:
        crop_clean = crop.lower().strip()
        
        # 1. Map and check crop support
        try:
            mapped_commodity = self._map_crop(crop_clean)
        except ValueError as e:
            raise ValueError(str(e))
            
        if self.model_bundle is None:
            raise RuntimeError("Market forecasting model is not initialized/loaded.")
            
        model = self.model_bundle['model']
        feature_names = self.model_bundle['feature_names']
        encoders = self.model_bundle['encoders']
        latest_prices_db = self.model_bundle['latest_prices_db']
        
        # Find latest record for this commodity in the pre-compiled DB
        # Group by APMC or take first available
        mandi_records = [r for r in latest_prices_db if r['Commodity'] == mapped_commodity]
        if not mandi_records:
            raise ValueError(f"Insufficient historical data points for commodity '{mapped_commodity}'.")
            
        # Select first matching APMC record
        record = mandi_records[0]
        apmc = record['APMC']
        current_price = float(record['modal_price'])
        
        # Build features for inference: t+1 forecast
        # We use current date/month as model inputs
        now = datetime.datetime.now()
        current_month = now.month
        current_year = now.year
        
        # Encode Commodity and APMC
        try:
            crop_encoded = encoders['Commodity'].transform([mapped_commodity])[0]
        except Exception:
            crop_encoded = encoders['Commodity'].transform(['unseen'])[0]
            
        try:
            apmc_encoded = encoders['APMC'].transform([apmc])[0]
        except Exception:
            apmc_encoded = encoders['APMC'].transform(['unseen'])[0]
            
        input_data = {
            'Commodity': crop_encoded,
            'APMC': apmc_encoded,
            'Month_num': current_month,
            'Year': current_year,
            'price_lag_1': current_price,
            'price_lag_2': float(record['price_lag_1']),
            'price_rolling_mean_3': float(record['price_rolling_mean_3'])
        }
        
        df_input = pd.DataFrame([input_data])[feature_names]
        
        # 2. TIME-SERIES MODEL PREDICTION
        price_forecast_30d = float(model.predict(df_input)[0])
        # Compute a realistic 7-day forecast interpolated between today and 30-day forecast
        price_forecast_7d = round(current_price + ((price_forecast_30d - current_price) / 4.0), 2)
        
        # Compute trend direction
        if price_forecast_30d > current_price * 1.02:
            trend = "Upward"
        elif price_forecast_30d < current_price * 0.98:
            trend = "Downward"
        else:
            trend = "Stable"
            
        # 3. Dynamic best-selling month estimation
        # We map known historical crop patterns
        best_months = {
            'Banana': "August/September (Onam Festival Spike)",
            'Paddy-Unhusked': "November/December (Makarajyothi crop post-monsoon)",
            'Coconut': "April/May (Dry summer oil extraction peak)",
            'Ginger (Fresh)': "December/January",
            'Turmeric': "March/April"
        }
        best_month = best_months.get(mapped_commodity, "December")
        
        # 4. Generate historical prices chart points using real lag data from model database
        historical_prices = self._generate_historical_prices(mapped_commodity, current_price, float(record['price_lag_1']), float(record['price_lag_2']), float(record['price_rolling_mean_3']))
        
        # Base cultivation costs & yields per acre (constants derived from Kerala Agri guidelines)
        base_costs_per_acre = {
            'Paddy-Unhusked': 22000, 'Coconut': 15000, 'Banana': 35000, 'Ginger (Fresh)': 45000, 'Turmeric': 40000
        }
        base_yields_per_acre = {
            'Paddy-Unhusked': 2000, 'Coconut': 3500, 'Banana': 6000, 'Ginger (Fresh)': 4000, 'Turmeric': 3000
        }
        
        investment = base_costs_per_acre.get(mapped_commodity, 25000) * farm_area_acres
        expected_yield = base_yields_per_acre.get(mapped_commodity, 1500) * farm_area_acres
        
        revenue = round(expected_yield * current_price, 2)
        profit = round(revenue - investment, 2)
        
        return {
            "crop": crop.capitalize(),
            "investment_cost": investment,
            "expected_revenue": revenue,
            "projected_profit": profit,
            "current_market_price": round(current_price, 2),
            "price_forecast_7d": price_forecast_7d,
            "price_forecast_30d": round(price_forecast_30d, 2),
            "demand_level": "High" if profit > 40000 else "Stable",
            "price_trend": trend,
            "best_selling_month": best_month,
            "historical_prices": historical_prices,
            "harvest_cycle_months": 4 if crop_clean in ['rice', 'paddy', 'banana'] else 8,
            "model_version": "Time-Series-RF-v1.0"
        }

    def _generate_historical_prices(self, commodity: str, current_price: float, lag1: float, lag2: float, rolling3: float) -> List[Dict[str, Any]]:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        current_month_idx = datetime.datetime.now().month - 1
        
        data = []
        for i in range(5, -1, -1):
            m_idx = (current_month_idx - i) % 12
            month_name = months[m_idx]
            
            # Map deterministic past values based on lag features from model db
            if i == 0:
                historical_price = current_price
            elif i == 1:
                historical_price = lag1
            elif i == 2:
                historical_price = lag2
            else:
                historical_price = round(rolling3 * (1.0 - (i - 2) * 0.01), 2)  # Stable approximation beyond lag2
            
            data.append({
                "month": month_name,
                "price": historical_price
            })
        return data

market_agent = MarketAgent()

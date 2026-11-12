import sys
import os
import unittest
from unittest.mock import MagicMock

# Adjust path to import backend app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml.crop_agent import crop_agent
from app.ml.disease_agent import disease_agent
from app.ml.fertilizer_agent import fertilizer_agent

class TestAgriGenieAgents(unittest.TestCase):
    
    def setUp(self):
        import cv2
        import numpy as np
        # Create dummy image files on disk for OpenCV to read
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        # Paint a green circle representing a leaf
        cv2.circle(img, (150, 150), 100, (0, 128, 0), -1)
        cv2.imwrite("test_sigatoka_leaf.jpg", img)
        cv2.imwrite("pepper_quick_wilt_spot.png", img)

    def tearDown(self):
        # Clean up temporary test image files
        for filename in ["test_sigatoka_leaf.jpg", "pepper_quick_wilt_spot.png"]:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass

    def test_crop_agent_recommendation(self):
        print("\nTesting Crop Intelligence Agent...")
        db_mock = MagicMock()
        # Mocking the query results to simulate no history
        db_mock.query().filter().order_by().all.return_value = []

        result_list = crop_agent.recommend(
            db=db_mock, farm_id=1,
            n=100.0, p=55.0, k=130.0, ph=6.8, 
            organic_carbon=0.6, boron=0.2, iron=4.5, zinc=0.6,
            temp=26.0, humidity=80.0, rainfall=1500.0, season='Kharif'
        )
        
        self.assertGreater(len(result_list), 0)
        top_crop = result_list[0]
        
        self.assertIn("crop_name", top_crop)
        self.assertIn("confidence_score", top_crop)
        self.assertIn("expected_yield", top_crop)
        self.assertIn("shap_contributions", top_crop)
        
        shap = top_crop["shap_contributions"]
        self.assertIn("nitrogen", shap)
        self.assertIn("potassium", shap)
        print("-> Crop Agent Success: Correctly suggested banana with SHAP.")

    def test_disease_agent_heuristics(self):
        print("\nTesting Disease Detection Agent (ConvGeM-NeXt)...")
        result = disease_agent.analyze_image("test_sigatoka_leaf.jpg")
        self.assertIn("detected_disease", result)
        self.assertIn("confidence", result)
        self.assertIn("severity_level", result)
        self.assertIn("treatment_plan", result)
        self.assertEqual(result["model"], "ConvGeM-NeXt")
        self.assertIn("recovery_time_days", result)
        
        result_wilt = disease_agent.analyze_image("pepper_quick_wilt_spot.png")
        self.assertIn("detected_disease", result_wilt)
        self.assertEqual(result_wilt["model"], "ConvGeM-NeXt")
        
        # Test non-existent image handling
        with self.assertRaises(FileNotFoundError):
            disease_agent.analyze_image("nonexistent_clean_leaf.png")
        print("-> Disease Agent Success: Correctly executed ConvGeM-NeXt leaf diagnostics.")

    def test_fertilizer_agent_calculations(self):
        print("\nTesting Smart Fertilizer Agent...")
        result = fertilizer_agent.calculate_fertilizer(
            crop="banana", n=30.0, p=20.0, k=40.0, ph=5.5,
            temperature=27.5, humidity=70.0
        )
        self.assertEqual(result["n_status"], "Deficient")
        self.assertEqual(result["p_status"], "Deficient")
        self.assertEqual(result["k_status"], "Deficient")
        self.assertGreater(len(result["fertilizer_schedule"]), 0)
        self.assertIn("estimated_cost", result)
        
        # Verify organic alternative exists in vegetative stage
        veg_stage = result["fertilizer_schedule"][1]
        self.assertIn("organic_alternatives", veg_stage)
        print("-> Fertilizer Agent Success: Correctly calculated NPK deficiencies.")

    def test_fertilizer_agent_missing_weather(self):
        print("\nTesting Smart Fertilizer Agent Missing Weather Error Handling...")
        with self.assertRaises(ValueError):
            fertilizer_agent.calculate_fertilizer(
                crop="banana", n=30.0, p=20.0, k=40.0, ph=5.5,
                temperature=None, humidity=None
            )
        print("-> Fertilizer Agent Success: Properly raised ValueError for missing weather data.")

    def test_market_agent_forecasting(self):
        print("\nTesting Market Forecasting Agent...")
        from app.ml.market_agent import market_agent
        
        # Test supported crop
        result = market_agent.get_market_forecast(crop="banana", district="Palakkad")
        self.assertEqual(result["crop"], "Banana")
        self.assertGreater(result["price_forecast_30d"], 0)
        self.assertIsNone(result["price_forecast_7d"]) # No 7-day interpolation
        self.assertIn("price_trend", result)
        self.assertGreater(len(result["historical_prices"]), 0)
        
        # Test unsupported crop / insufficient data
        with self.assertRaises(ValueError):
            market_agent.get_market_forecast(crop="rubber")
            
        print("-> Market Agent Success: Validated forecasts and handled unsupported crops.")

    def test_rag_engine_retrieval(self):
        print("\nTesting Bilingual RAG Engine...")
        from app.chatbot.rag_engine import rag_engine
        
        # Test semantic search retrieval
        res = rag_engine.process_query("കൊമ്പൻ ചെല്ലി")
        self.assertIsNotNone(res["kb_context"])
        self.assertEqual(res["intent"], "PEST_MANAGEMENT")
        self.assertGreater(res["retrieval_score"], 0.3)
        
        # Test response generation offline template
        from app.chatbot.response_generator import response_generator
        res = rag_engine.process_query("Is neem oil effective against whiteflies?")
        response = response_generator.generate_response(res)
        self.assertIn("neem", response.lower())
        print("-> RAG Engine Success: Retrieved matched localized context.")

if __name__ == '__main__':
    unittest.main()

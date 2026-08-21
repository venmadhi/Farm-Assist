import sys
import os
import unittest
from unittest.mock import MagicMock

# Adjust path to import backend app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ml.intent_classifier import intent_classifier
from app.ml.retriever import retriever
from app.chatbot.rag_engine import rag_engine
from app.chatbot.response_generator import response_generator

class TestRAGPipeline(unittest.TestCase):
    def test_intent_classification(self):
        # Verify classification matches semantic intents
        res_crop = intent_classifier.predict("Which crop gives better profit this season?")
        self.assertEqual(res_crop["intent"], "CROP_RECOMMENDATION")
        
        res_fert = intent_classifier.predict("എന്റെ മണ്ണിൽ പൊട്ടാസ്യം കുറവാണ് എന്ത് ചെയ്യണം?")
        self.assertEqual(res_fert["intent"], "FERTILIZER")
        
        res_dis = intent_classifier.predict("vazhaila yellow color varunnu")
        self.assertEqual(res_dis["intent"], "DISEASE")
        
        res_out = intent_classifier.predict("Who is the Prime Minister of India?")
        self.assertEqual(res_out["intent"], "UNKNOWN")

    def test_semantic_retrieval(self):
        # Verify documents are retrieved properly based on keyword/intent matching
        matches = retriever.retrieve("jeevamrutham prepare", intent="FERTILIZER")
        self.assertGreater(len(matches), 0)
        best_doc = matches[0][0]
        self.assertIn("Jeevamrutham", best_doc["title"])

    def test_rag_processing_with_mock_farmer(self):
        # Set up a mock farmer and database session
        mock_farmer = MagicMock()
        mock_farmer.id = 1
        mock_farmer.full_name = "Hari Vignesh"
        
        # Mock Farm
        mock_farm = MagicMock()
        mock_farm.id = 1
        mock_farm.location_district = "Palakkad"
        mock_farm.soil_type = "Laterite"
        mock_farm.land_area_acres = 1.5
        mock_farm.irrigation_type = "manual"
        mock_farm.water_availability = "medium"

        # Mock SoilTest
        mock_soil = MagicMock()
        mock_soil.nitrogen = 50
        mock_soil.phosphorus = 30
        mock_soil.potassium = 80
        mock_soil.ph = 6.2
        mock_soil.organic_carbon = 0.5
        
        mock_db = MagicMock()
        # Set up chain calls
        mock_db.query().filter().first.return_value = mock_farm
        mock_db.query().filter().order_by().first.return_value = mock_soil
        mock_db.query().filter().order_by().limit().all.return_value = []
        
        rag_data = rag_engine.process_query(
            query="ente nellinu entha valam venam?",
            db=mock_db,
            farmer=mock_farmer
        )
        
        self.assertEqual(rag_data["detected_language"], "THANGLISH")
        self.assertEqual(rag_data["intent"], "FERTILIZER")
        self.assertGreater(len(rag_data["kb_context"]), 0)
        self.assertIn("Farmer Name: Hari Vignesh", rag_data["farmer_context"])

    def test_response_generator_grounding(self):
        mock_rag_data = {
            "intent": "FERTILIZER",
            "detected_language": "ENGLISH",
            "language_preference": "ENGLISH",
            "conversation_context": "",
            "realtime_context": "",
            "original_query": "how to prepare jeevamrutham",
            "kb_context": "Document Title: Organic Soil - Jeevamrutham\nEnglish Content: In a 200L barrel, mix 10kg cow dung, 5L cow urine, 2kg jaggery.",
            "farmer_context": "Farmer Name: Hari Vignesh\nLocation District: Palakkad"
        }
        
        # Test offline fallback generation
        offline_answer = response_generator.generate_response(mock_rag_data, api_key=None)
        self.assertIn("Hari Vignesh", offline_answer)
        self.assertIn("cow dung", offline_answer)

if __name__ == '__main__':
    unittest.main()

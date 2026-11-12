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
        # Verify classification separates agricultural sub-intents.
        res_crop = intent_classifier.predict("Which crop gives better profit this season?")
        self.assertEqual(res_crop["intent"], "CROP_SELECTION")
        
        res_fert = intent_classifier.predict("എന്റെ മണ്ണിൽ പൊട്ടാസ്യം കുറവാണ് എന്ത് ചെയ്യണം?")
        self.assertEqual(res_fert["intent"], "FERTILIZER_RECOMMENDATION")
        
        res_dis = intent_classifier.predict("vazhaila yellow color varunnu")
        self.assertEqual(res_dis["intent"], "DISEASE_IDENTIFICATION")
        
        res_out = intent_classifier.predict("Who is the Prime Minister of India?")
        self.assertEqual(res_out["intent"], "UNKNOWN")

        expected_intents = {
            "it was wrong": "NEGATIVE_FEEDBACK",
            "that's not right": "NEGATIVE_FEEDBACK",
            "no": "NEGATIVE_FEEDBACK",
            "thanks": "THANKS",
            "which crop is best": "CROP_SELECTION",
            "crop health": "CROP_HEALTH_CHECK",
            "soil test report": "SOIL_TEST_INTERPRETATION",
            "what crop should I grow?": "CROP_SELECTION",
            "which crop is suitable for clay soil?": "CROP_SELECTION",
            "which soil is best for paddy": "SOIL_SUITABILITY",
            "how to control aphids in paddy": "PEST_CONTROL",
            "paddy leaves are turning brown": "DISEASE_IDENTIFICATION",
            "how much fertilizer for paddy": "FERTILIZER_RECOMMENDATION",
            "when should I irrigate paddy": "IRRIGATION",
            "best crop for clay soil": "CROP_SELECTION",
            "why are my paddy leaves yellow?": "DISEASE_IDENTIFICATION",
            "how much urea should I apply to paddy?": "FERTILIZER_RECOMMENDATION",
            "how to control rice stem borer?": "PEST_CONTROL",
            "what disease is affecting my coconut leaf?": "DISEASE_IDENTIFICATION",
            "how much water does paddy need?": "WATER_REQUIREMENT",
            "which crop is profitable in Palakkad?": "CROP_SELECTION",
            "rice is best or not": "CROP_SUITABILITY",
            "which fertilizer is best for paddy": "FERTILIZER_RECOMMENDATION",
        }
        for query, expected in expected_intents.items():
            self.assertEqual(intent_classifier.predict(query)["intent"], expected, query)

    def test_meta_feedback_bypasses_retrieval(self):
        for query in ["it was wrong", "that's not right", "no", "thanks"]:
            rag_data = rag_engine.process_query(query)
            answer = response_generator.generate_response(rag_data, api_key=None)
            self.assertTrue(rag_data["bypass_rag"])
            self.assertEqual(rag_data["kb_context"], "")
            self.assertNotIn("verified guidelines", answer.lower())

        feedback = response_generator.generate_response(
            rag_engine.process_query("it was wrong"), api_key=None
        )
        self.assertIn("Sorry", feedback)

    def test_semantic_retrieval(self):
        # Verify documents are retrieved properly based on keyword/intent matching
        matches = retriever.retrieve("jeevamrutham prepare", intent="ORGANIC_FARMING")
        self.assertGreater(len(matches), 0)
        best_doc = matches[0][0]
        self.assertIn("Jeevamrutham", best_doc["title"])

    def test_paddy_soil_retrieval_is_intent_and_crop_matched(self):
        query = "which soil is best for paddy"
        intent = intent_classifier.predict(query)["intent"]
        matches = retriever.retrieve(query, intent=intent, crop_entity="rice")

        self.assertEqual(intent, "SOIL_SUITABILITY")
        self.assertGreater(len(matches), 0)
        self.assertIn("Soil Suitability", matches[0][0]["title"])
        self.assertTrue(all("neem" not in document["title"].lower() for document, _ in matches))

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
        self.assertEqual(rag_data["intent"], "FERTILIZER_RECOMMENDATION")
        self.assertGreater(len(rag_data["kb_context"]), 0)
        self.assertIn("Location District: Palakkad", rag_data["farmer_context"])

    def test_crop_selection_does_not_inherit_active_crop_or_profile_dump(self):
        mock_farmer = MagicMock()
        mock_farmer.id = 27
        mock_farmer.full_name = "Private Farmer"

        mock_farm = MagicMock()
        mock_farm.id = 27
        mock_farm.location_district = "Palakkad"
        mock_farm.soil_type = "Clayey"
        mock_farm.water_availability = "medium"
        mock_farm.land_area_acres = 2.0

        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = mock_farm

        rag_data = rag_engine.process_query("which crop is best", db=mock_db, farmer=mock_farmer)
        answer = response_generator.generate_response(rag_data, api_key=None)

        self.assertEqual(rag_data["intent"], "CROP_SELECTION")
        self.assertIsNone(rag_data["crop_entity"])
        self.assertIn("Crop choice should be based", answer)
        self.assertNotIn("Nitrogen", answer)
        self.assertNotIn("urea", answer.lower())
        self.assertNotIn("Farmer Name", answer)
        self.assertNotIn("Expected Profit", answer)

    def test_rice_suitability_answer_is_direct_and_conditional(self):
        mock_farmer = MagicMock()
        mock_farmer.id = 31
        mock_farm = MagicMock()
        mock_farm.id = 31
        mock_farm.location_district = "Palakkad"
        mock_farm.soil_type = "Laterite"
        mock_farm.water_availability = "medium"
        mock_farm.land_area_acres = 1.0
        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = mock_farm

        rag_data = rag_engine.process_query("paddy is best or not", db=mock_db, farmer=mock_farmer)
        answer = response_generator.generate_response(rag_data, api_key=None)

        self.assertEqual(rag_data["intent"], "CROP_SUITABILITY")
        self.assertIn("Paddy grows well", answer)

    def test_paddy_fertilizer_question_uses_fertilizer_guidance(self):
        rag_data = rag_engine.process_query("which fertilizer is best for paddy")
        answer = response_generator.generate_response(rag_data, api_key=None)

        self.assertEqual(rag_data["intent"], "FERTILIZER_RECOMMENDATION")
        self.assertEqual(rag_data["crop_entity"], "rice")
        self.assertIn("Paddy Nutrient and Fertilizer Management", answer)
        self.assertIn("soil test", answer.lower())
        self.assertNotIn("Which crop is best", answer)

    def test_new_post_harvest_question_asks_for_crop(self):
        farmer = MagicMock(id=401)
        rag_data = rag_engine.process_query("harvest the crop", farmer=farmer)
        answer = response_generator.generate_response(rag_data, api_key=None)

        self.assertEqual(rag_data["intent"], "POST_HARVEST")
        self.assertIsNone(rag_data["crop_entity"])
        self.assertIn("Which crop are you harvesting", answer)
        self.assertNotIn("paddy", answer.lower())

    def test_post_harvest_follow_up_uses_established_paddy_context(self):
        farmer = MagicMock(id=402)
        first = rag_engine.process_query("My paddy crop is ready", farmer=farmer)
        rag_engine.save_session_response(402, "My paddy crop is ready", "Understood.")
        follow_up = rag_engine.process_query("How should I harvest the crop?", farmer=farmer)
        answer = response_generator.generate_response(follow_up, api_key=None)

        self.assertEqual(first["crop_entity"], "rice")
        self.assertEqual(follow_up["crop_entity"], "rice")
        self.assertIn("paddy", answer.lower())
        self.assertIn("dry", answer.lower())

    def test_post_harvest_follow_up_preserves_banana_context(self):
        farmer = MagicMock(id=403)
        rag_engine.process_query("My banana crop is ready", farmer=farmer)
        rag_engine.save_session_response(403, "My banana crop is ready", "Understood.")
        follow_up = rag_engine.process_query("How should I harvest the crop?", farmer=farmer)
        answer = response_generator.generate_response(follow_up, api_key=None)

        self.assertEqual(follow_up["crop_entity"], "banana")
        self.assertIn("For banana", answer)
        self.assertNotIn("mature paddy", answer)

    def test_off_topic_queries_bypass_retrieval_and_refuse(self):
        for query in ["help me write Python code", "Who is the Prime Minister of India?"]:
            rag_data = rag_engine.process_query(query)
            answer = response_generator.generate_response(rag_data, api_key=None)

            self.assertEqual(rag_data["intent"], "UNKNOWN")
            self.assertTrue(rag_data["bypass_rag"])
            self.assertEqual(rag_data["kb_context"], "")
            self.assertIn("farming questions only", answer)

    def test_malayalam_off_topic_query_refuses_in_malayalam(self):
        rag_data = rag_engine.process_query("രാഷ്ട്രീയ വാർത്തകൾ പറയൂ")
        answer = response_generator.generate_response(rag_data, api_key=None)

        self.assertEqual(rag_data["intent"], "UNKNOWN")
        self.assertEqual(rag_data["language_preference"], "MALAYALAM")
        self.assertIn("കൃഷി", answer)

    def test_response_generator_grounding(self):
        mock_rag_data = {
            "intent": "ORGANIC_FARMING",
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
        self.assertIn("cow dung", offline_answer)
        self.assertNotIn("Farmer Name", offline_answer)

    def test_response_generator_rejects_mislabeled_retrieval(self):
        mismatched = {
            "intent": "FERTILIZER_RECOMMENDATION",
            "detected_language": "ENGLISH",
            "language_preference": "ENGLISH",
            "conversation_context": "",
            "realtime_context": "",
            "original_query": "give fertilizer advice for paddy",
            "kb_context": "Document Title: Neem Oil Garlic Emulsion\nEnglish Content: Spray neem oil and garlic against aphids and caterpillars.",
            "farmer_context": "",
        }
        answer = response_generator.generate_response(mismatched, api_key=None)
        self.assertNotIn("neem oil", answer.lower())
        self.assertIn("No verified reference is available", answer)

    def test_response_generator_rejects_soil_content_for_crop_selection(self):
        mismatched = {
            "intent": "CROP_SELECTION",
            "detected_language": "ENGLISH",
            "language_preference": "ENGLISH",
            "conversation_context": "",
            "realtime_context": "",
            "original_query": "which crop should I grow",
            "kb_context": "Document Title: Paddy Soil pH\nEnglish Content: Rice grows in clay loam with suitable soil pH.",
            "farmer_context": "",
        }
        answer = response_generator.generate_response(mismatched, api_key=None)
        self.assertNotIn("pH", answer)
        self.assertIn("No verified reference is available", answer)

    def test_response_generator_uses_one_verified_document(self):
        data = {
            "intent": "ORGANIC_FARMING",
            "detected_language": "ENGLISH",
            "language_preference": "ENGLISH",
            "conversation_context": "",
            "realtime_context": "",
            "original_query": "how to prepare jeevamrutham",
            "kb_context": (
                "Document Title: Jeevamrutham\nEnglish Content: Mix cow dung and jaggery.\n\n"
                "Document Title: Neem Spray\nEnglish Content: Spray neem oil against aphids."
            ),
            "farmer_context": "",
        }
        answer = response_generator.generate_response(data, api_key=None)
        self.assertIn("cow dung", answer)
        self.assertNotIn("neem oil", answer.lower())

    def test_paddy_rain_harvest_question_uses_post_harvest_route(self):
        query = (
            "Heavy monsoon rains are forecast for Palakkad over the next three days, "
            "but my Paddy (Rice) crop is fully ready. How can I safely harvest and "
            "store the wet grains to prevent fungal rot and spoilage?"
        )
        rag_data = rag_engine.process_query(query)
        answer = response_generator.generate_response(rag_data, api_key=None)

        self.assertEqual(rag_data["intent"], "POST_HARVEST")
        self.assertIn("HARVESTING", rag_data["intents"])
        self.assertIn("DRYING", rag_data["intents"])
        self.assertIn("STORAGE", rag_data["intents"])
        self.assertIn("WEATHER_AGRICULTURE", rag_data["intents"])
        self.assertEqual(rag_data["crop_entity"], "rice")
        self.assertIn("dry", answer.lower())
        self.assertIn("mould", answer.lower())
        self.assertNotIn("correctly matched reference", answer)

if __name__ == '__main__':
    unittest.main()

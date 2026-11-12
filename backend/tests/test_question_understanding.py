import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.chatbot.rag_engine import RAGEngine
from app.chatbot.response_generator import response_generator
from app.chatbot.tts_engine import tts_engine


class TestQuestionUnderstanding(unittest.TestCase):
    def setUp(self):
        self.engine = RAGEngine()

    def test_short_crop_suitability_is_agricultural(self):
        data = self.engine.process_query("apple is best or not")
        answer = response_generator.generate_response(data)
        self.assertEqual(data["intent"], "CROP_SUITABILITY")
        self.assertEqual(data["crop_entity"], "apple")
        self.assertNotIn("farming questions only", answer.lower())

    def test_new_harvest_question_requires_crop(self):
        data = self.engine.process_query("harvest the crop")
        answer = response_generator.generate_response(data)
        self.assertEqual(data["intent"], "POST_HARVEST")
        self.assertIsNone(data["crop_entity"])
        self.assertIn("Which crop", answer)

    def test_harvest_follow_up_resolves_paddy(self):
        farmer = MagicMock(id=8101)
        self.engine.process_query("My paddy crop is ready", farmer=farmer)
        self.engine.save_session_response(8101, "My paddy crop is ready", "Understood")
        data = self.engine.process_query("How should I harvest it?", farmer=farmer)
        answer = response_generator.generate_response(data)
        self.assertEqual(data["crop_entity"], "rice")
        self.assertIn("paddy", answer.lower())

    def test_multi_intent_rain_harvest_query(self):
        data = self.engine.process_query(
            "My paddy is ready and heavy rain is coming. How do I harvest and store it?"
        )
        self.assertEqual(data["crop_entity"], "rice")
        self.assertEqual(data["intent"], "POST_HARVEST")
        self.assertTrue({"HARVESTING", "POST_HARVEST", "DRYING", "STORAGE"}.issubset(set(data["intents"])))

    def test_malayalam_crop_questions(self):
        cases = [
            ("\\u0d28\\u0d46\\u0d32\\u0d4d\\u0d32\\u0d4d \\u0d0e\\u0d2a\\u0d4d\\u0d2a\\u0d34\\u0d3e\\u0d23\\u0d4d \\u0d15\\u0d4a\\u0d2f\\u0d4d\\u0d2f\\u0d23\\u0d02?", "rice"),
            ("\\u0d24\\u0d46\\u0d19\\u0d4d\\u0d19\\u0d3f\\u0d28\\u0d4d \\u0d0f\\u0d24\\u0d4d \\u0d35\\u0d33\\u0d02 \\u0d35\\u0d47\\u0d23\\u0d4d\\u0d1f\\u0d24\\u0d4d?", "coconut"),
            ("\\u0d06\\u0d2a\\u0d4d\\u0d2a\\u0d3f\\u0d7e \\u0d15\\u0d43\\u0d37\\u0d3f \\u0d1a\\u0d46\\u0d2f\\u0d4d\\u0d2f\\u0d3e\\u0d7b \\u0d2a\\u0d31\\u0d4d\\u0d31\\u0d41\\u0d2e\\u0d4b?", "apple"),
        ]
        for escaped_query, crop in cases:
            data = self.engine.process_query(escaped_query.encode().decode("unicode_escape"))
            self.assertEqual(data["crop_entity"], crop)
            self.assertNotEqual(data["intent"], "UNKNOWN")

    def test_off_topic_is_rejected(self):
        for query in ["tell me a joke", "write Python code", "what is bitcoin"]:
            data = self.engine.process_query(query)
            answer = response_generator.generate_response(data)
            self.assertEqual(data["intent"], "UNKNOWN")
            self.assertIn("farming questions only", answer.lower())

    def test_tts_fallback_is_script_aware(self):
        english = tts_engine.get_speech_config("Apply fertilizer", "THANGLISH")
        malayalam = tts_engine.get_speech_config("\\u0d35\\u0d33\\u0d02".encode().decode("unicode_escape"), "MIXED")
        self.assertEqual(english["lang"], "en-IN")
        self.assertEqual(malayalam["lang"], "ml-IN")
        self.assertEqual(malayalam["status"], "configured")


if __name__ == "__main__":
    unittest.main()

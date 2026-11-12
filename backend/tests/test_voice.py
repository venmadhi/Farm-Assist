import sys
import os
import unittest

# Adjust path to import backend app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chatbot.voice_processor import voice_processor
from app.chatbot.tts_engine import tts_engine

class TestVoiceSystem(unittest.TestCase):
    def setUp(self):
        # Create dummy sound files to test the transcription filesystem checks
        for filename in ["banana_yellow.wav", "nellu_valam.wav", "unknown_audio.wav"]:
            with open(filename, "w") as f:
                f.write("mock audio bytes")

    def tearDown(self):
        # Clean up files
        for filename in ["banana_yellow.wav", "nellu_valam.wav", "unknown_audio.wav"]:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass

    def test_audio_transcription(self):
        # Test mock audio mapping
        res1 = voice_processor.transcribe_audio("banana_yellow.wav")
        self.assertEqual(res1["status"], "success")
        self.assertIn("banana", res1["transcript"])
        
        # Test default general fallback
        res2 = voice_processor.transcribe_audio("unknown_audio.wav")
        self.assertEqual(res2["status"], "success")
        self.assertGreater(len(res2["transcript"]), 0)

    def test_tts_engine_configuration(self):
        # Malayalam script query
        config_ml = tts_engine.get_speech_config(
            text="കുമ്മായം ചേർക്കുക",
            detected_language="MALAYALAM",
            preference="AUTO"
        )
        self.assertEqual(config_ml["lang"], "ml-IN")
        
        # English query
        config_en = tts_engine.get_speech_config(
            text="Apply dolomite",
            detected_language="ENGLISH",
            preference="AUTO"
        )
        self.assertEqual(config_en["lang"], "en-IN")
        
        # Forced preference
        config_forced = tts_engine.get_speech_config(
            text="Apply dolomite",
            detected_language="MALAYALAM",
            preference="ENGLISH"
        )
        self.assertEqual(config_forced["lang"], "en-IN")

    def test_tts_text_is_voice_safe(self):
        config = tts_engine.get_speech_config(
            text="**First:** Apply 20ml/L. 😊\n- Confirm the label.",
            detected_language="ENGLISH",
            preference="AUTO"
        )
        self.assertNotIn("**", config["text"])
        self.assertNotIn("😊", config["text"])
        self.assertNotIn("-", config["text"])

if __name__ == '__main__':
    unittest.main()

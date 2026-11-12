import re

class TTSEngine:
    def __init__(self):
        # Default speech configurations
        self.configs = {
            "MALAYALAM": {
                "lang_code": "ml-IN",
                "rate": 0.9,      # Malayalam sounds better slightly slower
                "pitch": 1.0,
                "voice_name": "Microsoft Shaji - Malayalam (India)"
            },
            "ENGLISH": {
                "lang_code": "en-IN",
                "rate": 1.0,
                "pitch": 1.0,
                "voice_name": "Microsoft Heera - English (India)"
            },
            "THANGLISH": {
                "lang_code": "en-IN",
                "rate": 0.95,
                "pitch": 1.0,
                "voice_name": "Microsoft Heera - English (India)"
            },
            "MIXED": {
                "lang_code": "en-IN",
                "rate": 0.95,
                "pitch": 1.0,
                "voice_name": "Microsoft Heera - English (India)"
            }
        }

    def get_speech_config(self, text: str, detected_language: str, preference: str = "AUTO") -> dict:
        """
        Determines the optimal TTS settings based on user preference and detected query language.
        Supported preferences: AUTO, MALAYALAM, ENGLISH
        """
        pref = preference.upper()
        
        if pref == "MALAYALAM":
            selected_lang = "MALAYALAM"
        elif pref == "ENGLISH":
            selected_lang = "ENGLISH"
        else: # AUTO
            if detected_language in {"MALAYALAM", "ENGLISH"}:
                selected_lang = detected_language
            elif detected_language in {"THANGLISH", "MIXED"}:
                selected_lang = "MALAYALAM" if re.search(r"[\u0d00-\u0d7f]", text) else "ENGLISH"
            else:
                selected_lang = "ENGLISH"
                
        config = self.configs[selected_lang].copy()
        
        speech_text = self.clean_for_speech(text)

        # Return TTS metadata config for the frontend Web Speech API client to synthesize speech
        return {
            "text": speech_text,
            "lang": config["lang_code"],
            "rate": config["rate"],
            "pitch": config["pitch"],
            "voice_preference": config["voice_name"],
            "status": "configured"
        }

    @staticmethod
    def clean_for_speech(text: str) -> str:
        """Convert display-oriented formatting into natural spoken text."""
        cleaned = re.sub(r"[*_`#]", "", text)
        cleaned = re.sub(r"(?m)^\s*[-•]\s*", "", cleaned)
        cleaned = re.sub(r"(?m)^\s*\d+[.)]\s*", "", cleaned)
        cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

tts_engine = TTSEngine()

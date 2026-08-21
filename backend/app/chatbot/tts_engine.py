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
                "lang_code": "ml-IN",  # Read Thanglish using Malayalam-accented voices or mixed styles
                "rate": 0.95,
                "pitch": 1.0,
                "voice_name": "Microsoft Shaji - Malayalam (India)"
            },
            "MIXED": {
                "lang_code": "ml-IN",
                "rate": 0.95,
                "pitch": 1.0,
                "voice_name": "Microsoft Shaji - Malayalam (India)"
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
            if detected_language in self.configs:
                selected_lang = detected_language
            else:
                selected_lang = "ENGLISH"
                
        config = self.configs[selected_lang].copy()
        
        # Return TTS metadata config for the frontend Web Speech API client to synthesize speech
        return {
            "text": text,
            "lang": config["lang_code"],
            "rate": config["rate"],
            "pitch": config["pitch"],
            "voice_preference": config["voice_name"],
            "status": "configured"
        }

tts_engine = TTSEngine()

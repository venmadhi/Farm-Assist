import re

class LanguageDetector:
    def __init__(self):
        # A dictionary of common Thanglish words
        self.thanglish_words = {
            "ente", "nellinu", "valam", "vazha", "vaazha", "krishi", "ila", "manja", "kurav", "kuravaanu",
            "vellam", "vellom", "cheyyan", "kodukkanam", "pattumo", "aayi", "kandathu", "engane", "eppo",
            "ippo", "cheythu", "vere", "enthelum", "enthayirikkum", "mazha", "kooduthal", "aanu", "ini",
            "entha", "cheyyendath", "soilil", "potassium", "nitrogen", "phosphorus", "acid", "chara",
            "charam", "chiyyala", "chichil", "pindi", "unni", "pindiunni", "vaattam", "kooman", "chellu",
            "elam", "ela", "nellu", "thandu", "thurappan", "kayathurappan", "puzhu", "prev", "krishibhavan",
            "jaiva", "chana", "chanakam", "gomuthram", "kanji", "vellam", "vlam", "valamanu", "thodukkaruth"
        }
        
        # A dictionary of common English words
        self.english_words = {
            "what", "is", "the", "how", "why", "which", "suitable", "recommendation", "recommend", "fertilizer",
            "crop", "disease", "price", "profit", "prevent", "control", "organic", "farming", "soil", "NPK",
            "potassium", "nitrogen", "phosphorus", "acidity", "yield", "paddy", "coconut", "banana", "pepper",
            "rubber", "cardamom", "ginger", "pests", "insect", "emulsion", "garlic", "neem", "oil", "bugs",
            "caterpillar", "government", "schemes", "scheme", "subsidy", "insurance", "rate", "cost", "today",
            "market", "trend", "current", "best", "selling", "season", "moisture", "temperature", "rainfall"
        }

    def detect(self, text: str) -> str:
        text_clean = text.lower().strip()
        if not text_clean:
            return "ENGLISH"

        # Check for Malayalam Unicode range (\u0d00 to \u0d7f)
        has_malayalam = bool(re.search(r'[\u0d00-\u0d7f]', text_clean))
        # Check for English/Latin alphabetic characters
        has_english = bool(re.search(r'[a-z]', text_clean))

        if has_malayalam and not has_english:
            return "MALAYALAM"
        
        if has_malayalam and has_english:
            return "MIXED"

        # If it only contains English characters, distinguish between English and Thanglish
        words = re.findall(r'[a-z]+', text_clean)
        if not words:
            return "ENGLISH"

        thanglish_count = 0
        english_count = 0
        
        for w in words:
            if w in self.thanglish_words:
                thanglish_count += 1
            elif w in self.english_words:
                english_count += 1

        # If we have a clear majority of Thanglish vocabulary, it's Thanglish
        if thanglish_count > 0 and thanglish_count >= english_count:
            return "THANGLISH"
        elif english_count > 0 and english_count > thanglish_count:
            # Check for structural patterns like mixed language (e.g. "ente soilil nitrogen low aanu")
            # If there's at least one Thanglish indicator, and many English words, classify as MIXED or THANGLISH
            if any(w in self.thanglish_words for w in words):
                return "MIXED"
            return "ENGLISH"
            
        # Default fallback: check if typical Thanglish words are substrings
        for w in words:
            if any(t in w for t in ["nell", "valam", "krishi", "vazha", "kurav", "engane", "kodukk"]):
                return "THANGLISH"

        return "ENGLISH"

language_detector = LanguageDetector()

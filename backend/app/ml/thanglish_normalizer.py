import re

class ThanglishNormalizer:
    def __init__(self):
        # Protected scientific/technical words that should not have suffixes stripped
        self.protected_words = {
            "potassium", "nitrogen", "phosphorus", "magnesium", "calcium", "boron", "iron", 
            "zinc", "bordeaux", "carbendazim", "propiconazole", "trichoderma", "metarhizium",
            "medium", "premium"
        }
        
        # Phonetic and synonym mapping from Thanglish/Manglish to standardized terms
        self.word_map = {
            # Banana
            "vaazha": "vazha",
            "vaza": "vazha",
            "vazhaila": "vazha ila",
            "vazhakk": "vazha",
            "vazhayude": "vazha",
            # Water
            "vellom": "vellam",
            "velam": "vellam",
            # Fertilizer
            "vlam": "valam",
            "valam": "valam",
            "valamanu": "valam",
            "valamkodukkanam": "valam kodukkanam",
            "fertilizer": "valam",
            "fertiliser": "valam",
            # Crop/Paddy
            "nellinu": "nellu",
            "nellu": "nellu",
            "nel": "nellu",
            "paddy": "nellu",
            "paddykk": "nellu",
            "paddiyil": "nellu",
            # Leaves/Leaf
            "ilakal": "ila",
            "ilayude": "ila",
            "ila": "ila",
            "leaf": "ila",
            "leafil": "ila",
            "leafin": "ila",
            # Disease/Pest
            "disease": "disease",
            "puzhu": "puzhu",
            "puru": "puzhu",
            "chellu": "chellu",
            "kooman": "chellu",
            "vaattam": "vattom",
            "wilt": "vattom",
            "blight": "blight",
            "sigatoka": "sigatoka",
            "segatoka": "sigatoka",
            # Deficiency/Low
            "kurav": "kuravu",
            "kurava": "kuravu",
            "kuravaanu": "kuravu",
            "low": "kuravu",
            "kuravanu": "kuravu",
            # Weather
            "mazha": "mazha",
            "rain": "mazha",
            # Price/Market
            "price": "vila",
            "rate": "vila",
            "rateil": "vila",
            "vilakku": "vila",
            "vila": "vila",
            # General
            "manja": "manja",
            "yellow": "manja",
            "karutha": "karuppu",
            "black": "karuppu",
            "spot": "spot",
            "spots": "spot",
            "profite": "profit",
            "profitable": "profit",
            "kodukkanam": "kodukkuka",
            "kodukka": "kodukkuka",
            "cheyyan": "cheyyuka",
            "cheyya": "cheyyuka",
            "pattumo": "sadhikkumo",
            "entha": "enthu",
            "enthaan": "enthu",
            "enthokke": "enthu",
            "enganeya": "engane"
        }

    def normalize(self, text: str) -> str:
        text_clean = text.lower().strip()
        # Remove special characters except alphanumeric and basic spaces
        text_clean = re.sub(r'[^a-zA-Z0-9\s\u0d00-\u0d7f]', '', text_clean)
        
        words = text_clean.split()
        normalized_words = []
        
        for w in words:
            # Check if word contains non-ASCII (e.g. Malayalam Unicode) - don't translate these here
            if bool(re.search(r'[\u0d00-\u0d7f]', w)):
                normalized_words.append(w)
                continue
                
            # If word is in map, normalize it
            if w in self.word_map:
                normalized_words.append(self.word_map[w])
            else:
                # Handle suffixes (e.g., "soilil" -> "soil", "vazhayude" -> "vazha")
                w_stripped = w
                if w not in self.protected_words:
                    for suffix in ["il", "in", "ude", "kk", "nte", "inu", "um", "anu", "aayi"]:
                        if w.endswith(suffix) and len(w) > len(suffix) + 2:
                            w_stripped = w[:-len(suffix)]
                            break
                
                if w_stripped in self.word_map:
                    normalized_words.append(self.word_map[w_stripped])
                else:
                    normalized_words.append(w_stripped)
                    
        return " ".join(normalized_words)

thanglish_normalizer = ThanglishNormalizer()

import os
import json
import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class EmbeddingModel:
    def __init__(self):
        self.fallback_vectorizer = None
        self.kb_texts = []
        self.fit_fallback_vectorizer()

    def fit_fallback_vectorizer(self):
        """
        Loads the local knowledge base and fits a TF-IDF character-level vectorizer.
        This provides a zero-dependency offline fallback embedding system.
        """
        try:
            ml_dir = os.path.dirname(os.path.abspath(__file__))
            kb_path = os.path.abspath(os.path.join(ml_dir, "..", "knowledge_base", "kerala_agriculture_kb.json"))
            
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                    
                for a in articles:
                    # Combine topics, tags, keywords, English and Malayalam contents
                    combined_text = f"{a.get('topic', '')} {a.get('crop', '')} {' '.join(a.get('tags', []))} {' '.join(a.get('keywords', []))} {a.get('content', '')} {a.get('malayalam_content', '')}"
                    self.kb_texts.append(combined_text)
            
            # If KB is empty, add default sentences
            if not self.kb_texts:
                self.kb_texts = [
                    "jeevamrutham cow dung organic fertilizer soil acidity lime",
                    "rhinoceros beetle pest control coconut palms crown metarhizium",
                    "quick wilt black pepper phytophthora bordeaux mixture",
                    "banana pseudostem weevil pindi unni stem borer neem oil",
                    "rubber tapping rain guarding ethrel latex yield panel dryness",
                    "cardamom capsule borer pest elam idukki shadow control",
                    "rice yellow stem borer thandu thurappan chlorantraniliprole",
                    "ginger soft rot rhizome rot seed treatment mancozeb"
                ]
                
            # Fit char n-gram vectorizer for robust misspelling and cross-lingual overlap match
            self.fallback_vectorizer = TfidfVectorizer(
                ngram_range=(2, 4), 
                analyzer='char_wb',
                max_features=512
            )
            self.fallback_vectorizer.fit(self.kb_texts)
        except Exception as e:
            print(f"Error fitting fallback vectorizer: {e}")

    def get_embedding(self, text: str, api_key: str = None) -> np.ndarray:
        """
        Calculates text embeddings.
        - Primary: Gemini API embeddings (multilingual semantic match)
        - Fallback: Local TF-IDF n-gram vector
        """
        if api_key:
            try:
                # Call Gemini embedding endpoint
                url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
                payload = {
                    "model": "models/text-embedding-004",
                    "content": {
                        "parts": [{
                            "text": text
                        }]
                    }
                }
                response = requests.post(url, json=payload, timeout=8)
                if response.status_code == 200:
                    data = response.json()
                    emb = data['embedding']['values']
                    return np.array(emb, dtype=np.float32)
                else:
                    print(f"Gemini embedding API warning: status {response.status_code}. Using fallback.")
            except Exception as e:
                print(f"Gemini embedding calculation failed: {e}. Using fallback.")

        # --- OFFLINE FALLBACK EMBEDDING ---
        if self.fallback_vectorizer:
            try:
                vec = self.fallback_vectorizer.transform([text]).toarray()[0]
                # Normalize vector to unit length
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                return vec.astype(np.float32)
            except Exception as e:
                print(f"Fallback embedding calculation failed: {e}")
                
        # Default zero array if all else fails
        return np.zeros(512, dtype=np.float32)

embedding_model = EmbeddingModel()

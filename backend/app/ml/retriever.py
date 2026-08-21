import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from .embedding_model import embedding_model

class Retriever:
    def __init__(self):
        self.kb_articles = []
        self.cached_embeddings_key = None
        self.cached_embeddings = [] # List of np.ndarray
        self.load_kb()
        
    def load_kb(self):
        try:
            ml_dir = os.path.dirname(os.path.abspath(__file__))
            kb_path = os.path.abspath(os.path.join(ml_dir, "..", "knowledge_base", "kerala_agriculture_kb.json"))
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    self.kb_articles = json.load(f)
                print(f"Retriever loaded {len(self.kb_articles)} articles.")
            else:
                print("Warning: Knowledge base JSON file not found in retriever.")
                self.kb_articles = []
        except Exception as e:
            print(f"Error loading KB in retriever: {e}")
            self.kb_articles = []

    def build_kb_embeddings(self, api_key: str = None):
        """
        Builds and caches embeddings for the entire KB.
        Regenerates if the api_key presence changes (e.g., switched from offline to online).
        """
        mode_key = "gemini" if api_key else "offline"
        if self.cached_embeddings_key == mode_key and len(self.cached_embeddings) == len(self.kb_articles):
            return
            
        print(f"Building KB embeddings in {mode_key} mode...")
        self.cached_embeddings = []
        
        for a in self.kb_articles:
            # Construct a rich representative text for the article
            text = f"{a.get('topic', '')} {a.get('crop', '')} {' '.join(a.get('tags', []))} {' '.join(a.get('keywords', []))} {a.get('content', '')} {a.get('malayalam_content', '')}"
            emb = embedding_model.get_embedding(text, api_key=api_key)
            self.cached_embeddings.append(emb)
            
        self.cached_embeddings_key = mode_key
        print(f"Successfully cached {len(self.cached_embeddings)} embeddings.")

    def retrieve(self, query: str, intent: str = None, crop_entity: str = None, api_key: str = None, k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieves top-k relevant documents based on cosine similarity and metadata re-ranking.
        """
        if not self.kb_articles:
            return []
            
        # 1. Ensure embeddings are built
        self.build_kb_embeddings(api_key=api_key)
        
        # 2. Embed the query
        query_emb = embedding_model.get_embedding(query, api_key=api_key)
        
        # 3. Calculate cosine similarity
        similarities = []
        for emb in self.cached_embeddings:
            # Cosine similarity (since vectors are already normalized to unit length, this is just dot product)
            sim = float(np.dot(query_emb, emb))
            similarities.append(sim)
            
        # 4. RE-RANKING PIPELINE
        re_ranked = []
        query_clean = query.lower()
        
        for idx, article in enumerate(self.kb_articles):
            base_score = similarities[idx]
            boost = 0.0
            
            # Boost 1: Crop entity match (e.g., query mentions banana and article crop is banana)
            article_crop = article.get('crop', '').lower()
            if crop_entity and article_crop == crop_entity.lower():
                boost += 0.25
            elif article_crop != 'general' and article_crop in query_clean:
                boost += 0.20
                
            # Boost 2: Intent match
            # Map predicted intents to topics/keywords
            tags = [t.lower() for t in article.get('tags', [])]
            keywords = [kw.lower() for kw in article.get('keywords', [])]
            
            if intent == 'FERTILIZER_RECOMMENDATION':
                if any(t in tags or t in keywords for t in ['fertilizer', 'NPK', 'urea', 'potash', 'lime', 'dolomite', 'valam', 'organic']):
                    boost += 0.20
            elif intent == 'DISEASE_OR_DEFICIENCY':
                if any(t in tags or t in keywords for t in ['pest', 'disease', 'wilt', 'blight', 'sigatoka', 'rot', 'bacterial', 'puzhu', 'chellu']):
                    boost += 0.20
            elif intent == 'MARKET_PRICES':
                if any(t in tags or t in keywords for t in ['market', 'price', 'rate', 'vila', 'profit', 'cost']):
                    boost += 0.20
                    
            # Boost 3: Keyword overlaps
            overlap_count = 0
            for kw in keywords:
                if kw in query_clean:
                    overlap_count += 1
            boost += min(0.15, overlap_count * 0.05)
            
            final_score = base_score + boost
            re_ranked.append((article, final_score))
            
        # Sort by final score descending
        re_ranked.sort(key=lambda x: x[1], reverse=True)
        return re_ranked[:k]

retriever = Retriever()

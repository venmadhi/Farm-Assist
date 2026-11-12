import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union
from .embedding_model import embedding_model

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        self.kb_articles: List[Dict[str, Any]] = []
        self.cached_embeddings_key = None
        self.cached_embeddings: List[np.ndarray] = []
        self.load_kb()
        
    def load_kb(self):
        try:
            ml_dir = os.path.dirname(os.path.abspath(__file__))
            kb_path = os.path.abspath(os.path.join(ml_dir, "..", "knowledge_base", "kerala_agriculture_kb.json"))
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    self.kb_articles = json.load(f)
                for article in self.kb_articles:
                    article.setdefault("category", article.get("topic", "general_agriculture"))
                    article.setdefault("crop_aliases", [article.get("crop", "general")])
                    raw_intent = article.get("intent", [article.get("topic", "general_agriculture")])
                    if isinstance(raw_intent, str):
                        article["intent"] = [raw_intent]
                    elif isinstance(raw_intent, list):
                        article["intent"] = raw_intent
                    article.setdefault("region", "Kerala")
                    article.setdefault("state", "Kerala")
                    article.setdefault("country", "India")
                    article.setdefault("language", "English/Malayalam")
                    article.setdefault("authority", article.get("source_name", "Kerala Agricultural University"))
                    article.setdefault("source_type", "government/university/research")
                print(f"Retriever loaded {len(self.kb_articles)} articles.")
                self.cached_embeddings_key = None
                self.cached_embeddings = []
            else:
                print("Warning: Knowledge base JSON file not found in retriever.")
                self.kb_articles = []
        except Exception as e:
            print(f"Error loading KB in retriever: {e}")
            self.kb_articles = []

    def build_kb_embeddings(self, api_key: str = None):
        """
        Builds and caches embeddings for the entire KB.
        """
        mode_key = "gemini" if api_key else "offline"
        if self.cached_embeddings_key == mode_key and len(self.cached_embeddings) == len(self.kb_articles) and len(self.cached_embeddings) > 0:
            return
            
        print(f"Building KB embeddings in {mode_key} mode...")
        self.cached_embeddings = []
        
        for a in self.kb_articles:
            intents_str = " ".join(a.get('intent', [])) if isinstance(a.get('intent'), list) else str(a.get('intent', ''))
            aliases_str = " ".join(a.get('crop_aliases', []))
            text = (
                f"{a.get('title', '')} {a.get('topic', '')} {a.get('crop', '')} {aliases_str} "
                f"{intents_str} {' '.join(a.get('tags', []))} {' '.join(a.get('keywords', []))} "
                f"{a.get('content', '')} {a.get('malayalam_content', '')}"
            )
            emb = embedding_model.get_embedding(text, api_key=api_key)
            self.cached_embeddings.append(emb)
            
        self.cached_embeddings_key = mode_key
        print(f"Successfully cached {len(self.cached_embeddings)} embeddings.")

    def retrieve(
        self,
        query: str,
        intent: Optional[Union[str, List[str]]] = None,
        crop_entity: Optional[str] = None,
        api_key: Optional[str] = None,
        k: int = 3,
        structured_intent: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieves top-k relevant documents using multi-factor ranking formula.
        """
        if not self.kb_articles:
            return []
            
        self.build_kb_embeddings(api_key=api_key)

        query_clean = query.lower()
        
        domain = structured_intent.get("domain", "GENERAL_FARMING") if structured_intent else "GENERAL_FARMING"
        pest = structured_intent.get("pest") if structured_intent else None
        disease = structured_intent.get("disease") if structured_intent else None
        weed = structured_intent.get("weed") if structured_intent else None

        from .agriculture_entities import ALIASES as _ALIASES
        _crop_aliases_map: dict = {"paddy": "rice", "nellu": "rice"}
        for canonical, aliases in _ALIASES.items():
            for alias in aliases:
                _alias_lower = alias.lower()
                if _alias_lower not in _crop_aliases_map:
                    _crop_aliases_map[_alias_lower] = canonical
        for canonical in _ALIASES:
            _crop_aliases_map.setdefault(canonical, canonical)
        normalized_target_crop = _crop_aliases_map.get((crop_entity or "").lower(), (crop_entity or "").lower())

        query_emb = embedding_model.get_embedding(query, api_key=api_key)
        similarities = []
        for emb in self.cached_embeddings:
            sim = float(np.dot(query_emb, emb))
            similarities.append(sim)

        re_ranked: List[Tuple[Dict[str, Any], float]] = []

        for idx, article in enumerate(self.kb_articles):
            base_score = similarities[idx]
            
            doc_crop = str(article.get('crop', '')).lower()
            doc_crop = _crop_aliases_map.get(doc_crop, doc_crop)
            doc_crop_aliases = [c.lower() for c in article.get('crop_aliases', [])]
            doc_domain = str(article.get('domain', '')).upper()
            doc_intents = [i.upper() for i in article.get('intent', [])]
            doc_topic = str(article.get('topic', '')).lower()
            doc_tags = [t.lower() for t in article.get('tags', [])]
            doc_keywords = [kw.lower() for kw in article.get('keywords', [])]
            doc_title = str(article.get('title', '')).lower()
            doc_content = str(article.get('content', '')).lower()

            crop_match_bonus = 0.0
            domain_match_bonus = 0.0
            pest_disease_bonus = 0.0
            unrelated_domain_penalty = 0.0
            crop_mismatch_penalty = 0.0

            # --- A. CROP MATCH LOGIC ---
            if normalized_target_crop:
                if doc_crop == normalized_target_crop or normalized_target_crop in doc_crop_aliases or normalized_target_crop in doc_tags:
                    crop_match_bonus = 0.50
                elif doc_crop != "general" and doc_crop != normalized_target_crop:
                    crop_mismatch_penalty = 0.80
                elif doc_crop == "general":
                    if domain in ["FERTILIZER", "CROP_CULTIVATION", "POST_HARVEST_STORAGE", "PEST_MANAGEMENT", "CROP_DISEASE"]:
                        crop_mismatch_penalty = 0.40
            else:
                if doc_crop == "general":
                    crop_match_bonus = 0.20

            # --- B. DOMAIN & TOPIC MATCH LOGIC ---
            # Try to match new domain metadata or fallback to old intents
            domain_matched = False
            if doc_domain == domain or domain in doc_intents:
                domain_match_bonus = 0.60
                domain_matched = True
            
            # Secondary Topic Matches
            if not domain_matched:
                if domain == "FERTILIZER" and ("fertilizer" in doc_topic or any(t in doc_tags for t in ["fertilizer", "nutrient", "urea"])):
                    domain_match_bonus = 0.40
                    domain_matched = True
                elif domain == "WEED_MANAGEMENT" and ("weed" in doc_topic or "weed" in doc_tags):
                    domain_match_bonus = 0.40
                    domain_matched = True
                elif domain == "SOIL_WATER" and ("soil" in doc_topic or "water" in doc_topic or "irrigation" in doc_tags):
                    domain_match_bonus = 0.40
                    domain_matched = True
                elif domain == "PEST_MANAGEMENT" and ("pest" in doc_topic or "insect" in doc_tags):
                    domain_match_bonus = 0.40
                    domain_matched = True
                elif domain == "CROP_DISEASE" and ("disease" in doc_topic or "fungus" in doc_tags):
                    domain_match_bonus = 0.40
                    domain_matched = True
            
            # Penalize heavily if domain is totally wrong (Relevance Gate)
            if domain == "WEED_MANAGEMENT":
                if "weed" not in doc_title and "weed" not in doc_tags and "weed" not in doc_topic and "weed" not in doc_keywords and "weeds" not in doc_content:
                    unrelated_domain_penalty += 1.0 # REJECT
            if domain == "FERTILIZER":
                if "jeevamrutham" in doc_title or "jeevamrutham" in doc_tags:
                    if "jeevamrutham" not in query_clean and "ജീവാമൃതം" not in query_clean:
                        unrelated_domain_penalty += 0.80 # Reject general organic input for specific fertilizer

            # --- C. PEST / DISEASE / WEED MATCH ---
            if pest and (pest in doc_title or pest in doc_tags or pest in doc_keywords or pest in doc_content):
                pest_disease_bonus += 0.50
            if disease and (disease in doc_title or disease in doc_tags or disease in doc_keywords or disease in doc_content):
                pest_disease_bonus += 0.50
            if weed and (weed in doc_title or weed in doc_tags or weed in doc_keywords or weed in doc_content):
                pest_disease_bonus += 0.50

            overlap_count = sum(1 for kw in doc_keywords if kw in query_clean)
            keyword_bonus = min(0.15, overlap_count * 0.05)

            final_score = (
                base_score
                + crop_match_bonus
                + domain_match_bonus
                + pest_disease_bonus
                + keyword_bonus
                - unrelated_domain_penalty
                - crop_mismatch_penalty
            )

            if normalized_target_crop and doc_crop != "general" and doc_crop != normalized_target_crop:
                final_score = min(final_score, 0.10)

            # If penalty brought it down severely, it fails the gate
            if final_score > 0.30:
                re_ranked.append((article, final_score))

        re_ranked.sort(key=lambda x: x[1], reverse=True)
        selected = re_ranked[:k]

        logger.info(
            "RAG RETRIEVAL | QUERY: %s | DOMAIN: %s | CROP: %s | RETRIEVED: %s | SCORES: %s | TOP SOURCE: %s",
            query,
            domain,
            normalized_target_crop or "None",
            [a.get("title") for a, _ in selected],
            [round(s, 4) for _, s in selected],
            selected[0][0].get("source_name") if selected else "None"
        )
        return selected

retriever = Retriever()

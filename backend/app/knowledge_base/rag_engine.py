import os
import json
import re
import requests
from typing import Dict, Any, List, Tuple, Optional

class RAGEngine:
    def __init__(self):
        self.kb_data = []
        self.load_kb()

    def load_kb(self):
        try:
            kb_path = os.path.join(os.path.dirname(__file__), 'kerala_agriculture_kb.json')
            with open(kb_path, 'r', encoding='utf-8') as f:
                self.kb_data = json.load(f)
            print(f"RAG Knowledge Base loaded successfully with {len(self.kb_data)} articles.")
        except Exception as e:
            print(f"Error loading RAG Knowledge Base: {e}")
            self.kb_data = []

    def retrieve_context(self, query: str) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Calculates simple keyword match overlap score for English and Malayalam fields.
        Returns the best matching article and its score.
        """
        if not self.kb_data:
            return None, 0.0

        query_clean = query.lower().strip()
        
        # Tokenize query
        query_words = set(re.findall(r'\w+', query_clean))
        
        # Add special handles for Malayalam characters which might not match \w+ standard English characters
        malayalam_words = set(re.findall(r'[\u0d00-\u0d7f]+', query_clean))
        query_words = query_words.union(malayalam_words)

        best_article = None
        best_score = 0.0

        for article in self.kb_data:
            score = 0.0
            
            # Check crop tags matching
            for tag in article.get('tags', []):
                if tag.lower() in query_clean:
                    score += 2.0
                    
            # Check explicit keywords
            for kw in article.get('keywords', []):
                if kw.lower() in query_clean:
                    score += 1.5

            # Word overlap with Content & Title
            content_words = set(re.findall(r'\w+', article['content'].lower()))
            mal_content_words = set(re.findall(r'[\u0d00-\u0d7f]+', article['malayalam_content']))
            article_words = content_words.union(mal_content_words)
            
            overlap = query_words.intersection(article_words)
            score += len(overlap) * 0.5
            
            # Boost score if query contains words from the mal_query example
            mal_q_words = set(re.findall(r'[\u0d00-\u0d7f]+', article.get('malayalam_query', '')))
            mal_overlap = query_words.intersection(mal_q_words)
            score += len(mal_overlap) * 1.5

            if score > best_score:
                best_score = score
                best_article = article

        # Normalize score
        return best_article, best_score

    def generate_response(self, query: str, api_key: str = None) -> Dict[str, Any]:
        article, score = self.retrieve_context(query)
        
        # Determine language of query (check if Malayalam character set is present)
        is_malayalam = bool(re.search(r'[\u0d00-\u0d7f]', query))
        
        # If score is too low, we don't have matching articles in local KB
        has_context = article is not None and score > 1.5
        
        if api_key:
            # LLM API integration via Gemini API (if key is set)
            try:
                context_str = ""
                if has_context:
                    context_str = f"Context (English): {article['content']}\nContext (Malayalam): {article['malayalam_content']}"
                else:
                    context_str = "No specific local database entries matched. Please answer using general Kerala agricultural practices."
                
                system_prompt = (
                    "You are AgriGenie AI, an expert agricultural consultant for farmers in Kerala, India. "
                    "You provide highly personalized, scientifically accurate, and friendly farming advice. "
                    "Use the provided context when applicable. If the farmer asks in Malayalam, answer in Malayalam. "
                    "If they ask in English, answer in English. Be encouraging and clear."
                )
                
                # Call Gemini API
                url = f"https://generativetutorial.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                # Alternatively standard endpoint:
                # url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"System Guidelines:\n{system_prompt}\n\nContext:\n{context_str}\n\nFarmer Query:\n{query}"
                        }]
                    }]
                }
                
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    resp_json = response.json()
                    answer = resp_json['candidates'][0]['content']['parts'][0]['text']
                    return {
                        "response": answer,
                        "source": "Gemini 1.5 Flash (RAG)",
                        "matched_topic": article.get('title', article.get('topic')) if has_context else "General Advice"
                    }
            except Exception as e:
                print(f"Gemini API execution failed: {e}. Falling back to offline engine.")

        if has_context:
            topic = article.get('title', article.get('topic'))
            if is_malayalam:
                response_text = (
                    f"**വിഷയം: {topic}**\n\n"
                    f"പ്രിയ കർഷകാ, നിങ്ങളുടെ ചോദ്യത്തിന് അടിസ്ഥാനമായി കണ്ടെത്തിയ വിവരങ്ങൾ താഴെ നൽകുന്നു:\n\n"
                    f"{article['malayalam_content']}\n\n"
                    f"*ശ്രദ്ധിക്കുക: ഇത് കേരള കാർഷിക സർവകലാശാലാ നിർദേശങ്ങൾ അടിസ്ഥാനമാക്കി തയ്യാറാക്കിയതാണ്.*"
                )
            else:
                response_text = (
                    f"**Topic: {topic}**\n\n"
                    f"Dear Farmer, here is the verified agricultural guideline regarding your query:\n\n"
                    f"{article['content']}\n\n"
                    f"*Note: These recommendations are based on Kerala Agricultural University guidelines.*"
                )
            source = "Local Agriculture KB"
        else:
            topic = "General Support"
            if is_malayalam:
                response_text = (
                    "ക്ഷമിക്കണം, എന്റെ കയ്യിലുള്ള കേരള കാർഷിക ഗൈഡ്‌ലൈൻസിൽ ഈ വിവരങ്ങൾ ലഭ്യമല്ല. "
                    "സാധാരണയായി വാഴ, തെങ്ങ്, കുരുമുളക്, റബ്ബർ, ഏലം എന്നിവയുടെ കൃഷിരീതികളെയും രോഗങ്ങളെയും കുറിച്ചുള്ള വിവരങ്ങൾ ചോദിക്കാവുന്നതാണ്. "
                    "ഉദാഹരണത്തിന്: 'തെങ്ങിൻറെ കൊമ്പൻ ചെല്ലിയെ എങ്ങനെ തടയാം?' അല്ലെങ്കിൽ 'ജീവാമൃതം ഉണ്ടാക്കുന്നത് എങ്ങനെ?'"
                )
            else:
                response_text = (
                    "I couldn't find a matching entry in my local Kerala agricultural guidelines. "
                    "You can ask me about typical Kerala crops like Paddy, Coconut, Banana, Pepper, Rubber, Cardamom, and organic practices like Jeevamrutham preparation."
                )
            source = "Consultant Fallback Rules"

        return {
            "response": response_text,
            "source": f"Offline RAG ({source})",
            "matched_topic": topic
        }

# Singleton instance
rag_engine = RAGEngine()

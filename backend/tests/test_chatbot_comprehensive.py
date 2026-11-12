import pytest
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chatbot.rag_engine import RAGEngine
from app.ml.intent_classifier import intent_classifier
from unittest.mock import patch

@pytest.fixture
def rag_engine():
    return RAGEngine()

@pytest.fixture
def mock_cloudflare():
    with patch('app.chatbot.response_generator.ResponseGenerator._cloudflare_response') as mock_cf:
        mock_cf.return_value = "Mocked LLM Response"
        yield mock_cf

TEST_QUERIES = [
    # 1. Weather / Climate
    ("Is it going to rain tomorrow?", "WEATHER_CLIMATE", None, None),
    ("How will the heatwave affect my coconut yield?", "WEATHER_CLIMATE", "coconut", None),
    
    # 2. Crop Selection / Cultivation
    ("What is the best time to plant rice?", "CROP_CULTIVATION", "rice", None),
    ("Can I grow apples in my backyard in Kochi?", "CROP_CULTIVATION", "apple", None),
    
    # 3. Pest Management (The bug we fixed!)
    ("Is neem oil effective against whiteflies?", "PEST_MANAGEMENT", None, "whitefly"),
    ("My tomato leaves have small green insects. How to control them?", "PEST_MANAGEMENT", "tomato", "general pest"),
    
    # 4. Weed Management (The bug we fixed!)
    ("How do I control weeds in my banana field organically?", "WEED_MANAGEMENT", "banana", None),
    
    # 5. Soil & Water Management
    ("How often should I water my rubber plants?", "SOIL_WATER", "rubber", None),
    ("My field is waterlogged after the rain. What to do?", "SOIL_WATER", None, None),
    ("What is the recommended NPK dose for coconut trees?", "FERTILIZER", "coconut", None),
    ("Is Jeevamrutham good for paddy?", "CROP_CULTIVATION", "paddy", None),
    ("What is the current market price of black pepper in Kerala?", "MARKET_PRICING", "black pepper", None),
    
    # 8. Government Schemes & Subsidies
    ("How can I apply for PM-Kisan?", "GOVERNMENT_SCHEMES", None, None),
    ("Are there any subsidies for drip irrigation?", "GOVERNMENT_SCHEMES", None, None),
    
    # 9. Post-Harvest & Storage
    ("How to store harvested paddy without spoilage?", "POST_HARVEST_STORAGE", "paddy", None),
    
    # 10. Livestock
    ("What is the vaccination schedule for goats?", "LIVESTOCK", None, None),
    
    # 11. Multi-turn / Ambiguous Context
    ("My crop is not growing well", "CROP_CULTIVATION", None, None), # Should ask for clarification
    ("Help", "UNKNOWN", None, None), # Should ask for clarification
    
    # 12. Mixed Language
    ("enikku coconut valam recommendation tharamo?", "FERTILIZER", "coconut", None),
    
    # 13. Out of Scope
    ("What is the capital of France?", "UNKNOWN", None, None),
    ("I have a severe headache, what medicine should I take?", "UNKNOWN", None, None)
]

def test_intent_classification():
    """Verify that intent classifier properly routes the 20 diverse test cases."""
    for query, expected_domain, expected_crop, expected_pest in TEST_QUERIES:
        res = intent_classifier.predict(query)
        print(f"Query: {query}")
        print(f"Domain: {res['domain']} (Expected: {expected_domain})")
        print(f"Crop: {res['crop']} (Expected: {expected_crop})")
        
        assert res["domain"] == expected_domain, f"Failed on '{query}'. Expected {expected_domain}, got {res['domain']}"
        if expected_crop:
            assert res["crop"] == expected_crop, f"Failed on '{query}'. Expected crop {expected_crop}, got {res['crop']}"
        if expected_pest:
            assert res["pest"] == expected_pest, f"Failed on '{query}'. Expected pest {expected_pest}, got {res['pest']}"

def test_rag_pipeline_end_to_end(rag_engine, mock_cloudflare):
    """Run full RAG pipeline on the two bug-fix queries to ensure end-to-end flow."""
    # Test Bug 1: Weed vs Soil
    query1 = "How do I control weeds in my banana field organically?"
    response1 = rag_engine.process_query(query1)
    assert response1["intent"] == "WEED_MANAGEMENT"
    assert response1["crop_entity"] == "banana"
    
    # Test Bug 2: Neem oil + whiteflies
    query2 = "Is neem oil effective against whiteflies?"
    response2 = rag_engine.process_query(query2)
    assert response2["intent"] == "PEST_MANAGEMENT"
    assert response2["entities"]["pest"] == "whitefly"

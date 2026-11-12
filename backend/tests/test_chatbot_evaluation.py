import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chatbot.rag_engine import RAGEngine
from unittest.mock import patch

@pytest.fixture
def rag_engine():
    return RAGEngine()

# (query, expected_intent, expected_crop_or_None)
TEST_SUITE = [
    # WEATHER
    ("Will it rain in the next 3 days in Palakkad?", "WEATHER", None),
    ("Is this the right time to sow paddy in Kerala?", "CROP_SOWING", "paddy"),
    ("How do I protect my crop from an upcoming heatwave?", "HEATWAVE", None),
    ("What's the best irrigation schedule given current humidity?", "IRRIGATION", None),

    # PEST / WEED
    ("How do I control weeds in my banana field organically?", "WEED_MANAGEMENT", "banana"),
    ("What's the best trap crop for aphids?", "PEST_MANAGEMENT", None),
    ("Is neem oil effective against whiteflies?", "PEST_MANAGEMENT", None),
    ("How often should I spray pesticide during flowering stage?", "PEST_MANAGEMENT", None),

    # MARKET
    ("What's today's mandi price for pepper in Kerala?", "MARKET_PRICE", "pepper"),
    ("Where can I sell my ginger harvest for the best price?", "MARKET_SELLING", "ginger"),
    ("Should I sell now or store my produce and wait for better prices?", "MARKET_FORECAST", None),
    ("What's the MSP for paddy this season?", "MSP", "paddy"),

    # GOVERNMENT
    ("What subsidies are available for drip irrigation in Kerala?", "SUBSIDY", None),
    ("How do I apply for PM-KISAN?", "PM_KISAN", None),
    ("Are there crop insurance schemes for cocoa farmers?", "CROP_INSURANCE", "cocoa"),
    ("What documents do I need for a Kisan Credit Card?", "KCC", None),

    # SOIL / WATER
    ("How do I test my soil pH without a lab?", "SOIL_PH", None),
    ("My soil is waterlogged — what should I do?", "WATER_MANAGEMENT", None),
    ("Which crops suit sandy/laterite soil?", "CROP_RECOMMENDATION", None),
    ("How much water does a mature coconut tree need per week?", "IRRIGATION", "coconut"),

    # POST-HARVEST
    ("How do I store harvested chilli to prevent mold?", "STORAGE", "chilli"),
    ("What's the shelf life of fresh ginger without refrigeration?", "STORAGE", "ginger"),
    ("How do I dry cocoa pods properly?", "DRYING", "cocoa"),

    # LIVESTOCK
    ("What vaccination schedule should I follow for goats?", "LIVESTOCK", None),
    ("Can I get advice on poultry feed mix?", "POULTRY", None),
    
    # AMBIGUOUS
    ("crop is not growing well", "CLARIFICATION_REQUIRED", None),
    ("help", "CLARIFICATION_REQUIRED", None),
    
    # MULTILINGUAL
    ("என் வாழையின் இலை மஞ்சளாகிறது என்ன செய்ய வேண்டும்?", "DISEASE", "வாழை"),
    ("banana leaf yellow ആകുന്നു എന്ത് ചെയ്യണം?", "DISEASE", "banana"),
    ("Palakkad-il next 3 days മഴ ഉണ്ടാകുമോ?", "WEATHER", None),
    
    # OUT OF SCOPE
    ("What's the capital of France?", "OUT_OF_SCOPE", None),
    ("Can you diagnose my health issue?", "OUT_OF_SCOPE", None),
    ("Tell me a joke.", "OUT_OF_SCOPE", None)
]

def test_question_understanding(rag_engine):
    print("\n--- Question Understanding Evaluation ---")
    failed = []
    
    for query, expected_intent, expected_crop in TEST_SUITE:
        res = rag_engine.process_query(query)
        actual_intent = res["intent"]
        actual_crop = res["crop_entity"]
        
        ok = actual_intent == expected_intent
        
        if expected_crop and actual_crop:
            ok = ok and (expected_crop.lower() in actual_crop.lower() or actual_crop.lower() in expected_crop.lower())
        
        if not ok:
            failed.append({
                "query": query,
                "expected_intent": expected_intent,
                "actual_intent": actual_intent,
                "expected_crop": expected_crop,
                "actual_crop": actual_crop
            })
            
    if failed:
        print(f"FAILED {len(failed)} out of {len(TEST_SUITE)} tests")
        for f in failed:
            print(f"Query: {f['query']}\nExpected Intent: {f['expected_intent']}, Got: {f['actual_intent']}\nExpected Crop: {f['expected_crop']}, Got: {f['actual_crop']}\n")
        pytest.fail(f"Question understanding failed on {len(failed)} queries.")
    else:
        print("PASS: 100% Intent & Entity extraction.")

def test_contradiction_handling(rag_engine):
    # Multi-turn Rain contradiction
    rag_engine.sessions = {} # Clear state
    q1 = "My banana leaves are turning yellow"
    res1 = rag_engine.process_query(q1, farmer=type('obj', (object,), {'id': 1}))
    assert res1["crop_entity"] == "banana"
    
    q2 = "It's been raining a lot this week"
    rag_engine.process_query(q2, farmer=type('obj', (object,), {'id': 1}))
    assert rag_engine.sessions[1]["context"]["weather"] == "raining"
    
    q3 = "Actually, it hasn't rained for the last two days."
    rag_engine.process_query(q3, farmer=type('obj', (object,), {'id': 1}))
    assert rag_engine.sessions[1]["context"]["weather"] == "no rain"
    
    # Soil contradiction
    rag_engine.sessions = {}
    rag_engine.process_query("My soil is sandy.", farmer=type('obj', (object,), {'id': 2}))
    assert rag_engine.sessions[2]["context"]["soil"] == "sandy"
    
    rag_engine.process_query("Actually, it's clay soil.", farmer=type('obj', (object,), {'id': 2}))
    assert rag_engine.sessions[2]["context"]["soil"] == "clay"

def test_live_data_routing(rag_engine):
    # Weather
    res_weather = rag_engine.process_query("Will it rain in Palakkad in the next 3 days?")
    assert "current real-time weather in palakkad" in res_weather["realtime_context"].lower()
    
    # Market Price
    res_market = rag_engine.process_query("What's today's mandi price for pepper in Kerala?")
    assert "Verified Live Market Data" in res_market["realtime_context"] or "don't have verified" in res_market["realtime_context"] or "Insufficient" in res_market["realtime_context"]

def test_regression_sand_laterite(rag_engine):
    # Ensure it doesn't give a generic acid soil article when asked about crop suitability
    res = rag_engine.process_query("Which crops suit sandy/laterite soil?")
    assert res["intent"] == "CROP_RECOMMENDATION"

def test_regression_whitefly_neem(rag_engine):
    res = rag_engine.process_query("Is neem oil effective against whiteflies?")
    assert res["intent"] == "PEST_MANAGEMENT"
    assert res["entities"]["pest"] == "whitefly"

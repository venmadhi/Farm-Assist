import json
import os

kb_path = r"e:\farm assistant project\Farm-Assist-main\backend\app\knowledge_base\kerala_agriculture_kb.json"

with open(kb_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    intent = item.get("intent", [])
    if isinstance(intent, str):
        intent = [intent]
    
    domain = "GENERAL_FARMING"
    intents_str = " ".join(intent).upper()
    topic = item.get("topic", "").upper()
    tags = " ".join(item.get("tags", [])).upper()

    if "FERTILIZER" in intents_str or "NUTRIENT" in intents_str or "SOIL_HEALTH" in intents_str:
        domain = "FERTILIZER"
    elif "WEED" in intents_str or "WEED" in tags or "WEED" in topic:
        domain = "WEED_MANAGEMENT"
    elif "DISEASE" in intents_str:
        domain = "CROP_DISEASE"
    elif "PEST" in intents_str:
        domain = "PEST_MANAGEMENT"
    elif "WEATHER" in intents_str:
        domain = "WEATHER_CLIMATE"
    elif "MARKET" in intents_str or "PRICE" in intents_str:
        domain = "MARKET_PRICING"
    elif "GOVERNMENT" in intents_str or "SUBSIDY" in intents_str:
        domain = "GOVERNMENT_SCHEMES"
    elif "POST_HARVEST" in intents_str or "STORAGE" in intents_str:
        domain = "POST_HARVEST_STORAGE"
    elif "LIVESTOCK" in intents_str:
        domain = "LIVESTOCK"
    elif "SOIL" in intents_str or "WATER" in intents_str or "IRRIGATION" in intents_str:
        domain = "SOIL_WATER"
    elif "CROP_RECOMMENDATION" in intents_str or "SUITABILITY" in intents_str or "INPUT_PREPARATION" in intents_str or "ORGANIC_FARMING" in intents_str:
        domain = "CROP_CULTIVATION"

    item["domain"] = domain

with open(kb_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Updated {len(data)} records with domain.")

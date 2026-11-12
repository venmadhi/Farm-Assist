"""Canonical agricultural entities shared by routing, intent classification, and retrieval."""

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple, Set

ENTITY_GROUPS: Dict[str, Tuple[str, ...]] = {
    "cereal": ("paddy", "rice", "wheat", "maize", "corn", "ragi", "sorghum"),
    "fruit": (
        "banana", "mango", "apple", "pineapple", "papaya", "watermelon",
        "guava", "jackfruit", "orange", "grape"
    ),
    "plantation": (
        "coconut", "rubber", "arecanut", "cocoa", "coffee", "tea"
    ),
    "spice": (
        "black pepper", "pepper", "cardamom", "ginger", "turmeric",
        "clove", "cinnamon"
    ),
    "root_tuber": (
        "tapioca", "cassava", "sweet potato", "yam", "elephant foot yam"
    ),
    "vegetable": (
        "tomato", "brinjal", "eggplant", "chilli", "okra", "cucumber",
        "bitter gourd", "bottle gourd", "cabbage", "cauliflower", "beans",
        "carrot", "onion", "garlic", "potato"
    ),
}

# Canonical name -> Tuple of aliases (English variations, plural, Malayalam script, Thanglish/transliterations, scientific names)
ALIASES: Dict[str, Tuple[str, ...]] = {
    "coconut": (
        "coconuts", "coconut palm", "coconut tree", "coconut trees", "thengu", "thenginu",
        "thengukal", "thenginta", "thenginte", "thenga", "the coconut", "cocos nucifera",
        "തെങ്ങ്", "തെങ്ങിന്", "തെങ്ങിന്റെ", "തെങ്ങുകൾ", "തേങ്ങ", "തേങ്ങയ്ക്ക്", "തേങ്ങയുടെ", "നാളികേരം"
    ),
    "rice": (
        "paddy", "nellu", "nellinu", "nellinte", "rice crop", "rice plant", "paddy crop",
        "paddy field", "oryza sativa", "നെല്ല്", "നെല്ലിന്", "നെല്ലിന്റെ", "അരി", "പാടം"
    ),
    "banana": (
        "bananas", "plantain", "plantains", "vazha", "vazhaykk", "vazhakal", "vazhayude",
        "nendran", "grand naine", "robusta", "musa acuminata", "musa", "വാഴ", "വാഴയ്ക്ക്", "വാഴയുടെ", "വാഴകൾ", "നേന്ത്രൻ"
    ),
    "tomato": (
        "tomatoes", "thakkali", "thakkaali", "thakkalikku", "thakkaliye", "solanum lycopersicum",
        "തക്കാളി", "തക്കാളിക്ക്", "തക്കാളിയുടെ"
    ),
    "mango": (
        "mangoes", "manga", "mangifera indica", "mango tree", "mavu", "mavinu",
        "മാവ്", "മാവിന്", "മാങ്ങ", "മാങ്ങയ്ക്ക്"
    ),
    "papaya": (
        "papayas", "omakka", "kappanga", "carica papaya", "പപ്പായ", "ഓമയ്ക്ക", "കപ്പങ്ങ"
    ),
    "pineapple": (
        "pineapples", "kaithachakka", "ananas comosus", "കൈതച്ചക്ക", "പൈനാപ്പിൾ"
    ),
    "jackfruit": (
        "jackfruits", "plavu", "chakka", "artocarpus heterophyllus", "പ്ലാവ്", "പ്ലാവിന്", "ചക്ക"
    ),
    "guava": (
        "guavas", "perakka", "koyya", "psidium guajava", "പേരയ്ക്ക", "പേര"
    ),
    "watermelon": (
        "watermelons", "thannimathan", "citrullus lanatus", "തണ്ണിമത്തൻ", "വത്തക്ക"
    ),
    "orange": (
        "oranges", "madhuranaarakam", "citrus sinensis", "ഓറഞ്ച്", "നാരകം"
    ),
    "grape": (
        "grapes", "munthiri", "vitis vinifera", "മുന്തിരി", "മുന്തിരിങ്ങ"
    ),
    "tapioca": (
        "cassava", "kappa", "maracheeni", "manihot esculenta", "കപ്പ", "മരച്ചീനി"
    ),
    "sweet potato": (
        "sweet potatoes", "madhurakkizhangu", "ipomoea batatas", "മധുരക്കിഴങ്ങ്"
    ),
    "yam": (
        "elephant foot yam", "elephant yam", "chena", "kachil", "kaachil", "dioscorea",
        "amorphophallus paeoniifolius", "ചേന", "കാച്ചിൽ"
    ),
    "rubber": (
        "rubber tree", "hevea brasiliensis", "rubber pal", "റബ്ബർ", "റബ്ബറിന്", "റബ്ബറിന്റെ"
    ),
    "arecanut": (
        "areca nut", "adakka", "kamuku", "pakku", "areca catechu", "അടയ്ക്ക", "കമുക്", "പാക്ക്"
    ),
    "cocoa": (
        "cacao", "theobroma cacao", "കൊക്കോ"
    ),
    "coffee": (
        "coffee plant", "coffea", "കാപ്പി", "കാപ്പിച്ചെടി"
    ),
    "tea": (
        "tea plant", "camellia sinensis", "തേയില", "ചായ"
    ),
    "pepper": (
        "black pepper", "black peppers", "kurumulaku", "kurumulak", "piper nigrum", "കുരുമുളക്", "കുരുമുളകിന്"
    ),
    "cardamom": (
        "elam", "elakkaya", "elettaria cardamomum", "ഏലം", "ഏലക്ക"
    ),
    "ginger": (
        "inji", "zingiber officinale", "ഇഞ്ചി", "ഇഞ്ചിക്ക്"
    ),
    "turmeric": (
        "manjal", "curcuma longa", "മഞ്ഞൾ", "മഞ്ഞളിന്"
    ),
    "clove": (
        "cloves", "gramboo", "karayampoo", "syzygium aromaticum", "ഗ്രാമ്പൂ", "കരയാമ്പൂ"
    ),
    "cinnamon": (
        "karuvapatta", "cinnamomum verum", "കറുവപ്പട്ട"
    ),
    "brinjal": (
        "eggplant", "eggplants", "vazhutana", "vazhuthananga", "solanum melongena", "വഴുതന", "വഴുതനങ്ങ"
    ),
    "chilli": (
        "chili", "chillies", "green chilli", "mulaku", "pachamulaku", "capsicum", "മുളക്", "പച്ചമുളക്"
    ),
    "okra": (
        "ladyfinger", "lady's finger", "venda", "vendakka", "abelmoschus esculentus", "വെണ്ട", "വെണ്ടയ്ക്ക"
    ),
    "cucumber": (
        "cucumbers", "vellari", "vellarikka", "cucumis sativus", "വെള്ളരി", "വെള്ളരിക്ക"
    ),
    "bitter gourd": (
        "bittergourd", "pavakka", "kaippakka", "momordica charantia", "പാവയ്ക്ക", "കൈപ്പയ്ക്ക"
    ),
    "bottle gourd": (
        "bottlegourd", "churakka", "lagenaria siceraria", "ചുരയ്ക്ക"
    ),
    "cabbage": (
        "cabbages", "muttakkos", "brassica oleracea", "കാബേജ്", "മുട്ടക്കോസ്"
    ),
    "cauliflower": (
        "cauliflowers", "poovukos", "കോളീഫ്ലവർ", "പൂക്കോസ്"
    ),
    "beans": (
        "bean", "payar", "vanpayar", "cowpea", "പയർ", "വൻപയർ", "ബീൻസ്"
    ),
    "carrot": (
        "carrots", "daucus carota", "കാരറ്റ്"
    ),
    "onion": (
        "onions", "ulli", "savala", "cheriyulli", "allium cepa", "ഉള്ളി", "സവാള", "ചെറിയുള്ളി"
    ),
    "garlic": (
        "veluthulli", "allium sativum", "വെളുത്തുള്ളി"
    ),
    "potato": (
        "potatoes", "urulaikkizhangu", "urulaikizhang", "solanum tuberosum", "ഉരുളക്കിഴങ്ങ്"
    ),
    "maize": (
        "corn", "cholam", "makka cholam", "zea mays", "ചോളം", "മക്കച്ചോളം"
    ),
    "ragi": (
        "finger millet", "panjapullu", "eleusine coracana", "റാഗി", "പഞ്ഞപ്പുല്ല്"
    ),
    "wheat": (
        "gothambu", "triticum", "ഗോതമ്പ്"
    ),
    "sorghum": (
        "great millet", "cholam", "sorghum bicolor", "ചോളം"
    ),
    "apple": (
        "apples", "apple fruit", "apple crop", "apple tree", "malus domestica",
        "ആപ്പിൾ", "ആപ്പിളിന്റെ", "ആപ്പിളിന്"
    ),
}

CANONICAL_TO_GROUP: Dict[str, str] = {
    crop: group for group, crops in ENTITY_GROUPS.items() for crop in crops
}
for canonical in ALIASES:
    CANONICAL_TO_GROUP.setdefault(canonical, "crop")

def _variants(canonical: str, aliases: Iterable[str]) -> List[str]:
    return sorted({canonical, *aliases}, key=len, reverse=True)

def extract_crops(text: str) -> List[str]:
    """Return canonical crops mentioned in text, ordered by first occurrence."""
    if not text:
        return []
    lowered = text.lower()
    found: List[Tuple[int, str]] = []
    
    # Check aliases first
    for canonical, aliases in ALIASES.items():
        for variant in _variants(canonical, aliases):
            pattern = re.escape(variant.lower())
            # Match word boundary in ASCII and Malayalam character boundaries
            match = re.search(rf"(?<![\w\u0d00-\u0d7f]){pattern}(?![\w\u0d00-\u0d7f])", lowered)
            if match:
                found.append((match.start(), canonical))
                break

    # Check direct canonical names not covered above
    for canonical, group in CANONICAL_TO_GROUP.items():
        if canonical in ALIASES:
            continue
        match = re.search(rf"(?<![\w\u0d00-\u0d7f]){re.escape(canonical)}(?![\w\u0d00-\u0d7f])", lowered)
        if match:
            found.append((match.start(), canonical))

    return list(dict.fromkeys(crop for _, crop in sorted(found)))

def crop_group(crop: Optional[str]) -> Optional[str]:
    return CANONICAL_TO_GROUP.get(crop) if crop else None

def has_agricultural_entity(text: str) -> bool:
    return bool(extract_crops(text)) or bool(extract_pest(text)) or bool(extract_disease(text)) or bool(extract_weed(text)) or bool(extract_method_constraint(text))

def extract_location(text: str) -> Optional[str]:
    """Extract Kerala districts from text."""
    lowered = text.lower()
    districts = [
        "thiruvananthapuram", "kollam", "pathanamthitta", "alappuzha", "kottayam", "idukki",
        "ernakulam", "thrissur", "palakkad", "malappuram", "kozhikode", "wayanad", "kannur", "kasaragod",
        "kerala"
    ]
    for d in districts:
        if re.search(rf"(?<![\w]){d}(?![\w])", lowered):
            return d
    return None

def extract_time_reference(text: str) -> Optional[str]:
    """Extract time references for weather and market queries."""
    lowered = text.lower()
    if any(t in lowered for t in ["today", "current", "now", "today's", "ഇന്ന്"]):
        return "today"
    if any(t in lowered for t in ["tomorrow", "നാളെ"]):
        return "tomorrow"
    if any(t in lowered for t in ["next 3 days", "3 days", "coming days", "അടുത്ത 3 ദിവസം"]):
        return "next_3_days"
    if any(t in lowered for t in ["this week", "week", "ഈ ആഴ്ച"]):
        return "this_week"
    if any(t in lowered for t in ["this season", "season", "ഈ സീസൺ"]):
        return "this_season"
    return None

def extract_weather_condition(text: str) -> Optional[str]:
    """Extract weather conditions."""
    lowered = text.lower()
    if any(w in lowered for w in ["heatwave", "hot", "heat", "choodu", "ചൂട്"]):
        return "heatwave"
    if any(w in lowered for w in ["heavy rain", "flood", "rain", "storm", "monsoon", "mazha", "മഴ"]):
        return "rain"
    if any(w in lowered for w in ["drought", "dry", "varalcha", "വരൾച്ച"]):
        return "drought"
    if any(w in lowered for w in ["humidity", "humid", "eerppam"]):
        return "humidity"
    return None

def extract_growth_stage(text: str) -> Optional[str]:
    """Extract growth stage info."""
    lowered = text.lower()
    if any(s in lowered for s in ["seedling", "nursery", "planting", "തൈ"]):
        return "seedling"
    if any(s in lowered for s in ["flowering", "flower", "poov", "പൂവിടുന്ന"]):
        return "flowering"
    if any(s in lowered for s in ["fruiting", "fruit", "kaay", "കായ്ക്കുന്ന"]):
        return "fruiting"
    if any(s in lowered for s in ["mature", "ready", "harvest", "പാകമായ", "വിളവെടുപ്പ്"]):
        return "mature"
    return None

def extract_pest(text: str) -> Optional[str]:
    lowered = text.lower()
    pests = {
        "whitefly": ["whitefly", "whiteflies", "white fly", "white insects"],
        "aphid": ["aphid", "aphids", "plant lice", "green aphids"],
        "borer": ["borer", "shoot borer", "fruit borer", "stem borer", "തണ്ടുതുരപ്പൻ"],
        "beetle": ["beetle", "rhinocerous beetle", "ചെല്ലി", "കൊമ്പൻ ചെല്ലി"],
        "caterpillar": ["caterpillar", "puzhu", "പുഴു"],
        "mealybug": ["mealybug", "mealy bug", "mealy bugs", "white bug", "മീലിമൂട്ട"],
        "thrips": ["thrips", "ila pen", "ഇലപ്പേൻ"],
        "mite": ["mite", "mites", "mandari", "മണ്ഡരി"]
    }
    for pest, variants in pests.items():
        if any(re.search(rf"(?<![\w]){re.escape(v)}(?![\w])", lowered) for v in variants):
            return pest
    # General pest terms
    if any(p in lowered for p in ["pest", "insect", "bug", "കീടം"]):
        return "general pest"
    return None

def extract_disease(text: str) -> Optional[str]:
    lowered = text.lower()
    diseases = {
        "wilt": ["wilt", "wilting", "bacterial wilt", "fusarium wilt", "quick wilt", "വാട്ടം"],
        "blight": ["blight", "leaf blight", "kariyila", "കരിയൽ"],
        "rot": ["rot", "root rot", "stem rot", "fruit rot", "ചീയൽ", "മഹാളി"],
        "sigatoka": ["sigatoka", "yellow sigatoka"],
        "mildew": ["mildew", "powdery mildew", "downy mildew", "പൂപ്പൽ"],
        "rust": ["rust", "leaf rust"],
        "spot": ["leaf spot", "brown spot", "പുള്ളി"]
    }
    for disease, variants in diseases.items():
        if any(re.search(rf"(?<![\w]){re.escape(v)}(?![\w])", lowered) for v in variants):
            return disease
    if any(d in lowered for d in ["disease", "fungus", "virus", "bacteria", "രോഗം", "അണുബാധ"]):
        return "general disease"
    return None

def extract_weed(text: str) -> Optional[str]:
    lowered = text.lower()
    if any(w in lowered for w in ["weed", "weeds", "unwanted plants", "weed growth", "kala", "kalakal", "കള"]):
        return "weeds"
    return None

def extract_entities(text: str) -> Dict[str, Any]:
    """Master entity extraction for RAG/Routing."""
    crops = extract_crops(text)
    return {
        "crop": crops[0] if crops else None,
        "all_crops": crops,
        "location": extract_location(text),
        "time_reference": extract_time_reference(text),
        "weather_condition": extract_weather_condition(text),
        "growth_stage": extract_growth_stage(text),
        "method_constraint": extract_method_constraint(text),
        "commodity": extract_commodity(text),
        "data_type": classify_data_type(text),
        "pest": extract_pest(text),
        "disease": extract_disease(text),
        "weed": extract_weed(text),
    }


def extract_method_constraint(text: str) -> Optional[str]:
    """Extract farming method constraints (organic, chemical, manual)."""
    lowered = text.lower()
    if any(w in lowered for w in [
        "organic", "organically", "jaiva", "jeevamrutham", "panchagavya",
        "natural", "bio", "ജൈവ", "പ്രകൃതി", "neem oil", "neem extract", "neem-based"
    ]):
        return "organic"
    if any(w in lowered for w in [
        "chemical", "pesticide", "fungicide", "herbicide", "spray",
        "chemicals", "synthetic", "രാസ", "കീടനാശിനി"
    ]):
        return "chemical"
    if any(w in lowered for w in ["manual", "hand", "physical", "mechanically"]):
        return "manual"
    return None


def extract_commodity(text: str) -> Optional[str]:
    """Extract commodity/produce name for market queries (may differ from crop)."""
    lowered = text.lower()
    commodity_map = {
        "pepper": ["pepper", "kurumulaku", "black pepper", "കുരുമുളക്"],
        "rubber": ["rubber", "latex", "റബ്ബർ"],
        "cardamom": ["cardamom", "elam", "ഏലം"],
        "coconut": ["coconut", "copra", "thengu", "thenga", "കൊപ്ര", "തേങ്ങ"],
        "ginger": ["ginger", "inji", "ഇഞ്ചി"],
        "turmeric": ["turmeric", "manjal", "മഞ്ഞൾ"],
        "rice": ["rice", "paddy", "nellu", "അരി", "നെല്ല്"],
        "banana": ["banana", "vazha", "plantain", "nendran", "വാഴ"],
        "tomato": ["tomato", "thakkali", "തക്കാളി"],
        "coffee": ["coffee", "kaapi", "കാപ്പി"],
        "tea": ["tea", "theyila", "തേയില"],
        "arecanut": ["arecanut", "areca", "adakka", "betel nut", "അടക്ക"],
        "tapioca": ["tapioca", "cassava", "kappa", "മരച്ചീനി"],
    }
    for canonical, variants in commodity_map.items():
        if any(v in lowered for v in variants):
            return canonical
    # Fall back to crop extraction
    crops = extract_crops(text)
    return crops[0] if crops else None


# ────────────────────────────────────────────────────────────────────────────
# STATIC vs DYNAMIC data type classifier
# DYNAMIC  → needs live API data  (weather, market price, MSP, scheme status)
# STATIC   → can be answered from knowledge base
# ────────────────────────────────────────────────────────────────────────────
_DYNAMIC_INTENT_PATTERNS = [
    r"\b(today|tomorrow|tonight|current|right now|this week|next \d+ days?|this season)\b",
    r"\b(today'?s?|current|live|now|real.?time|forecast)\b",
    r"\b(mandi price|market price|rate today|today'?s? price|current price|current rate)\b",
    r"\b(msp|minimum support price|monthly price|this year'?s? price)\b",
    r"\b(will it rain|rain forecast|weather forecast|temperature today|humidity today)\b",
    r"\b(scheme|subsidy|insurance).{0,30}\b(current|2024|2025|2026|this year|available now)\b",
]
_DYNAMIC_PATTERNS_COMPILED = [re.compile(p, re.IGNORECASE) for p in _DYNAMIC_INTENT_PATTERNS]


def classify_data_type(text: str) -> str:
    """Returns 'DYNAMIC' if the question needs live data, else 'STATIC'."""
    for pattern in _DYNAMIC_PATTERNS_COMPILED:
        if pattern.search(text):
            return "DYNAMIC"
    # Also dynamic if explicit time references to the present
    time_ref = extract_time_reference(text)
    if time_ref in ("today", "tomorrow", "next_3_days"):
        return "DYNAMIC"
    return "STATIC"
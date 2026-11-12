import os

# Default to the final trained YOLO11 disease classification model
YOLO_DISEASE_MODEL_PATH = os.getenv("DISEASE_MODEL_PATH", r"E:\farm assistant project\models\disease_classifier\best.pt")
YOLO_TASK = os.getenv("YOLO_TASK", "classify")
YOLO_CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.15"))

# Comprehensive crop and disease mappings for all 19 crops supported by the crop classifier
# mapped against the 86 classes from the trained YOLO11 disease classification model
SUPPORTED_CROPS = {
    "rubber_tree": {
        "display_name": "Rubber",
        "aliases": ["rubber", "rubber tree", "rubber_tree", "hevea"],
        "disease_classes": [
            "canker", "canker rubber tree", "pink_disease", "brown_basttree_trunk",
            "dieback", "phytophthora", "stem_bleeding", "stem_cracking", "disease_trunk"
        ],
        "healthy_classes": ["healthy_rubber", "healthy_rubber_tree_trunk", "healthy_trunk", "healthy", "healthy_leaf"]
    },
    "rice": {
        "display_name": "Rice",
        "aliases": ["rice", "paddy", "nellu"],
        "disease_classes": [
            "blast", "leaf_blast", "leaf_blotch", "narrow_brown_spot", "narrow_brown",
            "bacterial_leaf_blight", "brown_spot", "stem_borer", "yellow_mottle_virus"
        ],
        "healthy_classes": ["healthy_rice", "healthy_leaves", "healthy", "healthy_leaf"]
    },
    "banana": {
        "display_name": "Banana",
        "aliases": ["banana", "vazha", "plantain"],
        "disease_classes": [
            "sigatoka", "segatoka infected", "cordana_leaf_spot", "anthracnose",
            "yellowing", "mosaic", "mosaic_virus", "bacterial_blight", "bacterial_spot"
        ],
        "healthy_classes": ["healthy_banana", "healthy", "healthy_leaf"]
    },
    "coffee": {
        "display_name": "Coffee",
        "aliases": ["coffee", "kaapi", "arabica", "robusta"],
        "disease_classes": [
            "leaf_rust", "rust", "brown_eye_spot", "brown_spot", "bicho_mineiro",
            "anthracnose", "black_rot", "sooty_mould", "dieback"
        ],
        "healthy_classes": ["healthy_coffee", "healthy", "healthy_leaf"]
    },
    "tomato": {
        "display_name": "Tomato",
        "aliases": ["tomato", "takkali"],
        "disease_classes": [
            "early_blight", "late_blight", "leaf_mold", "bacterial_spot", "bacterial_blight",
            "bacterial", "septoria_leaf_spot", "yellow_leaf_curl_virus", "fruit_rot",
            "fruit_cracking", "fruit_fasciation", "fruit_borer", "leaf_miner", "whitefly_infestation"
        ],
        "healthy_classes": ["healthy_tomato", "healthy", "healthy_leaf"]
    },
    "cassava": {
        "display_name": "Cassava / Tapioca",
        "aliases": ["cassava", "tapioca", "kappa", "maracheeni", "kolli"],
        "disease_classes": [
            "cassava_mosaic_disease", "cmd", "green_mottle", "mosaic", "mosaic_virus",
            "brown_streak", "bacterial_blight", "anthracnose"
        ],
        "healthy_classes": ["healthy_cassava", "healthy_tapioca", "healthy", "healthy_leaf"]
    },
    "arecanut": {
        "display_name": "Arecanut",
        "aliases": ["arecanut", "areca nut", "betel nut", "kamuku", "adakka"],
        "disease_classes": [
            "mahali_koleroga", "yellow_leaf_disease", "fruit_rot", "bud_borer",
            "stem_bleeding", "stem_cracking", "slow_decline", "yellowing"
        ],
        "healthy_classes": ["healthy_arecanut", "healthy_nut", "healthy_trunk", "healthy", "healthy_leaf"]
    },
    "black_pepper": {
        "display_name": "Black Pepper",
        "aliases": ["black_pepper", "black pepper", "kurumulaku", "pepper"],
        "disease_classes": [
            "phytophthora", "slow_decline", "slow decline", "quick wilt", "anthracnose",
            "pollu_disease", "damage_pest", "yellowing"
        ],
        "healthy_classes": ["healthy_black_pepper", "healthy", "healthy_leaf"]
    },
    "brinjal": {
        "display_name": "Brinjal (Eggplant)",
        "aliases": ["brinjal", "eggplant", "aubergine", "vazhuthananga"],
        "disease_classes": [
            "phomopsis_blight", "shoot_fruit_borer", "bacterial_wilt", "little_leaf",
            "fruit_borer", "leaf_spot", "whitefly_infestation", "aphid"
        ],
        "healthy_classes": ["healthy_brinjal", "healthy", "healthy_leaf"]
    },
    "chilli": {
        "display_name": "Chilli",
        "aliases": ["chilli", "chili", "pepper", "mulaku"],
        "disease_classes": [
            "anthracnose", "dieback", "fruit_rot", "leaf_curl", "powdery_mildew",
            "bacterial_spot", "aphid", "whitefly_infestation", "mosaic_virus"
        ],
        "healthy_classes": ["healthy_chilli", "healthy", "healthy_leaf"]
    },
    "cocoa": {
        "display_name": "Cocoa",
        "aliases": ["cocoa", "cacao"],
        "disease_classes": [
            "black_pod_rot", "black_pod_fungus", "brown_pod_fungus", "monilia",
            "pod_borer", "mirid_bug_damage", "dieback", "canker", "stem_blackening", "phytophthora"
        ],
        "healthy_classes": ["healthy_cocoa", "healthy", "healthy_leaf"]
    },
    "coconut": {
        "display_name": "Coconut",
        "aliases": ["coconut", "thengu", "nalikeram"],
        "disease_classes": [
            "bud_rot", "stem_bleeding", "wcwld_mild", "wcwld_moderate", "wcwld_severe",
            "wcwld_unspecified", "leaf_rot", "rhizome_rot", "dry_leaves_stress", "yellowing"
        ],
        "healthy_classes": ["healthy_coconut", "healthy_trunk", "healthy_nut", "healthy", "healthy_leaf"]
    },
    "ginger": {
        "display_name": "Ginger",
        "aliases": ["ginger", "inji"],
        "disease_classes": [
            "rhizome_rot", "bacterial_wilt", "soft_rot", "leaf_spot",
            "leaf_blight", "yellowing", "sclerotium_rot"
        ],
        "healthy_classes": ["healthy_ginger", "healthy", "healthy_leaf"]
    },
    "groundnut": {
        "display_name": "Groundnut",
        "aliases": ["groundnut", "peanut", "kadalakkayi"],
        "disease_classes": [
            "leaf_spot", "early_blight", "late_blight", "rust", "stem_rot",
            "collar_rot", "aphid", "mosaic"
        ],
        "healthy_classes": ["healthy_groundnut", "healthy", "healthy_leaf"]
    },
    "jackfruit": {
        "display_name": "Jackfruit",
        "aliases": ["jackfruit", "chakka", "plavu"],
        "disease_classes": [
            "fruit_rot", "rhizopus_rot", "pink_disease", "dieback", "leaf_spot",
            "leaf_cutting_weevil", "fruit_fly"
        ],
        "healthy_classes": ["healthy_jackfruit", "healthy", "healthy_leaf"]
    },
    "mango": {
        "display_name": "Mango",
        "aliases": ["mango", "mavu", "manga"],
        "disease_classes": [
            "anthracnose", "powdery_mildew", "dieback", "sooty_mould", "bacterial_canker",
            "gall_midge", "fruit_fly", "stem_borer", "leaf_cutting_weevil"
        ],
        "healthy_classes": ["healthy_mango", "healthy", "healthy_leaf"]
    },
    "pineapple": {
        "display_name": "Pineapple",
        "aliases": ["pineapple", "kaithachakka"],
        "disease_classes": [
            "heart_rot", "root_rot", "mealybug_wilt", "black_rot",
            "multiple_crown_disorder", "fruit_rot", "crown_rot", "yellowing"
        ],
        "healthy_classes": ["healthy_pineapple", "healthy", "healthy_leaf"]
    },
    "tea": {
        "display_name": "Tea",
        "aliases": ["tea", "chaya", "camellia"],
        "disease_classes": [
            "blister_blight", "black_rot", "brown_blight", "red_spider_mite",
            "mosquito_bug", "dieback", "pestalotiopsis_leaf_spot", "sooty_mould"
        ],
        "healthy_classes": ["healthy_tea", "healthy", "healthy_leaf"]
    },
    "turmeric": {
        "display_name": "Turmeric",
        "aliases": ["turmeric", "manjal"],
        "disease_classes": [
            "rhizome_rot", "leaf_spot", "leaf_blotch", "taphrina_leaf_spot",
            "shoot_borer", "yellowing", "sclerotium_rot"
        ],
        "healthy_classes": ["healthy_turmeric", "healthy", "healthy_leaf"]
    }
}

import os
import sys
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

# Add backend dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ml.crop_image_classifier import CropImageClassifier
from app.ml.yolo_disease_agent import YOLODiseaseClassifier
from app.ml.disease_config import SUPPORTED_CROPS

def test_pipeline(image_path):
    print(f"\n--- Testing Pipeline on: {os.path.basename(image_path)} ---")
    
    if not os.path.exists(image_path):
        print("Image not found!")
        return

    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # 1. Crop Classification
    print("\n[1] Running CropImageClassifier...")
    crop_classifier = CropImageClassifier()
    crop_result = crop_classifier.predict(image)
    print(f"Crop Result: {crop_result}")

    # 2. Disease Detection
    print("\n[2] Running YOLODiseaseClassifier...")
    disease_classifier = YOLODiseaseClassifier()
    disease_result = disease_classifier.predict(image)
    
    if not disease_result.get("success"):
        print(f"Disease Detection Failed: {disease_result.get('message', disease_result.get('reason'))}")
    else:
        prediction = disease_result.get("prediction", {})
        print(f"Disease Result: {prediction.get('disease')} (Confidence: {prediction.get('confidence')})")

    # 3. Validation Logic (as in disease.py)
    print("\n[3] Running Compatibility Validation...")
    crop_name = crop_result.get("crop", "Unknown")
    crop_key = crop_result.get("crop_key")
    crop_status = crop_result.get("status")
    
    raw_class = disease_result.get("raw_class", "")
    
    compatibility_status = "crop_uncertain"
    
    if crop_status == "low_confidence" or crop_name == "Unknown":
        compatibility_status = "crop_uncertain"
    elif prediction.get("disease") == "Healthy":
        compatibility_status = "consistent"
    elif crop_key and crop_key in SUPPORTED_CROPS and raw_class:
        crop_config = SUPPORTED_CROPS[crop_key]
        valid_classes = crop_config.get("disease_classes", []) + crop_config.get("healthy_classes", [])
        valid_classes = [vc.lower().replace("_", " ") for vc in valid_classes]
        pred_class_lower = raw_class.lower().replace("_", " ")
        is_compatible = any(vc in pred_class_lower for vc in valid_classes) or (crop_key in pred_class_lower)
        compatibility_status = "consistent" if is_compatible else "mismatch"
    else:
        compatibility_status = "mismatch"
        
    print(f"Final Compatibility Status: {compatibility_status}")


if __name__ == "__main__":
    test_img = r"E:\farm assistant project\Farm-Assist-main\backend\ml\datasets\crop_classification\valid\banana\20210218_160016_jpg.rf.THT4w6MGOUhRCBZkAhM6.jpg"
    test_pipeline(test_img)

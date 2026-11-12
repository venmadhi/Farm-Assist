import os
import random
import glob
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))

from app.ml.crop_image_classifier import CropImageClassifier
from app.ml.yolo_disease_agent import YOLODiseaseClassifier
from app.ml.disease_config import SUPPORTED_CROPS

def test_image(image_path, crop_classifier, yolo_classifier, true_label=None):
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Failed to open {image_path}: {e}")
        return

    print("-" * 50)
    print(f"Testing Image: {os.path.basename(image_path)}")
    if true_label:
        print(f"True Label (from dataset): {true_label}")

    # 1. Crop Classification
    crop_result = crop_classifier.predict(image)
    crop_name = crop_result.get("crop", "Unknown")
    crop_status = crop_result.get("status")
    crop_msg = crop_result.get("message", "")
    print(f"Crop Prediction: {crop_name} (Confidence: {crop_result.get('confidence', 0.0):.4f})")
    
    if crop_status in ["low_confidence", "error"] or crop_name == "Unknown":
        print(f"Crop Error Message: {crop_msg}")

    # 2. Disease Detection
    disease_result = yolo_classifier.predict(image, filename=os.path.basename(image_path))
    prediction = disease_result.get("prediction", {})
    raw_class = disease_result.get("raw_class", "")
    
    # 3. Compatibility Logic (similar to disease.py)
    compatibility_status = "crop_uncertain"
    crop_key = crop_result.get("crop_key")
    
    if crop_status in ["model_unavailable", "model_missing", "error"] or crop_name == "Unavailable":
        compatibility_status = "crop_uncertain"
    elif crop_status == "low_confidence" or crop_name == "Unknown":
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

    if compatibility_status in ["mismatch", "crop_uncertain"]:
        prediction["disease"] = "Unverified (Crop Mismatch)" if compatibility_status == "mismatch" else "Unverified (Unknown Crop)"
        prediction["confidence"] = 0.0
        prediction["severity"] = "Unknown"

    print(f"Final Disease Diagnosis: {prediction.get('disease')} (Confidence: {prediction.get('confidence', 0.0):.4f})")
    print(f"Compatibility Status: {compatibility_status}")

def main():
    print("Loading Models...")
    crop_classifier = CropImageClassifier()
    yolo_classifier = YOLODiseaseClassifier()

    dataset_val_dir = "E:\\leaf disease detection.yolov8\\valid"
    images_dir = os.path.join(dataset_val_dir, "images")
    labels_dir = os.path.join(dataset_val_dir, "labels")

    # Load class names
    import yaml
    with open("E:\\leaf disease detection.yolov8\\data.yaml", 'r') as f:
        data = yaml.safe_load(f)
    class_names = data.get('names', [])

    if os.path.exists(images_dir) and os.path.exists(labels_dir):
        image_files = glob.glob(os.path.join(images_dir, "*.jpg"))
        if len(image_files) > 5:
            image_files = random.sample(image_files, 5)

        for img_path in image_files:
            # Find corresponding label
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            label_path = os.path.join(labels_dir, base_name + ".txt")
            true_label_name = "Unknown"
            if os.path.exists(label_path):
                with open(label_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        class_id = int(content.split()[0])
                        if class_id < len(class_names):
                            true_label_name = class_names[class_id]
            
            test_image(img_path, crop_classifier, yolo_classifier, true_label=true_label_name)
    else:
        print("Validation dataset not found at expected path.")

    print("\n" + "="*50)
    print("TESTING OUT-OF-SCOPE IMAGE (Curry Leaf / Dummy)")
    
    # Check if a dummy image exists, if not, create one
    dummy_path = "curry_leaf_test.jpg"
    if not os.path.exists(dummy_path):
        # We will use an image from outside the dataset, e.g., something that doesn't look like the 7 crops
        # For this test script, we just generate a green image with noise to simulate an unrecognized leaf
        import numpy as np
        arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        arr[:, :, 1] = 200 # Make it very green
        Image.fromarray(arr).save(dummy_path)
    
    test_image(dummy_path, crop_classifier, yolo_classifier, true_label="Out of Scope (Curry Leaf Mock)")

if __name__ == "__main__":
    main()

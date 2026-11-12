import sys
import os
import glob
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
from app.ml.yolo_disease_agent import YOLODiseaseClassifier
from app.ml.disease_config import YOLO_DISEASE_MODEL_PATH

def main():
    print(f"Loading YOLO agent with model path: {YOLO_DISEASE_MODEL_PATH}")
    agent = YOLODiseaseClassifier(device="cpu")
    
    # Grab a few images from the validation set
    val_images = glob.glob(r"E:\leaf disease detection.yolov8\valid\images\*.jpg")
    if not val_images:
        val_images = glob.glob(r"E:\leaf disease detection.yolov8\valid\images\*.*")
    
    if not val_images:
        print("No validation images found!")
        return

    # Test top 3 images
    for i, img_path in enumerate(val_images[:3]):
        print(f"\n--- Testing Image {i+1}: {os.path.basename(img_path)} ---")
        img = Image.open(img_path)
        
        # We don't specify crop to test auto-detection / fallback
        res = agent.predict(img)
        print("Prediction Result:")
        for k, v in res.items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    main()

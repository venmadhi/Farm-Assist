import os
import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.ml.crop_image_classifier import CropImageClassifier
from app.ml.yolo_disease_agent import YOLODiseaseClassifier
from PIL import Image
import numpy as np

def main():
    # Create a dummy image
    img = Image.new('RGB', (224, 224), color = (73, 109, 137))
    img.save('dummy.jpg')
    
    print("Testing CropImageClassifier...")
    crop_clf = CropImageClassifier()
    res1 = crop_clf.predict(img)
    print("Crop result:", res1)
    
    print("\nTesting YOLODiseaseClassifier...")
    disease_clf = YOLODiseaseClassifier()
    res2 = disease_clf.predict(img)
    print("Disease result:", res2)
    
if __name__ == "__main__":
    main()

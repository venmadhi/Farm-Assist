from pathlib import Path
import os
import json

base_dir = Path(__file__).resolve().parent.parent.parent
print("Base dir:", base_dir)

model_path = base_dir / "ml" / "models" / "crop_classifier.keras"
classes_path = base_dir / "ml" / "models" / "crop_classes.json"

print(f"Model path: {model_path} - Exists: {model_path.exists()}")
print(f"Classes path: {classes_path} - Exists: {classes_path.exists()}")

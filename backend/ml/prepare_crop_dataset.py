import os
import shutil
import sys
import yaml
from pathlib import Path

# Paths
YOLO_DATASET_DIR = r"E:\leaf disease detection.yolov8"
OUTPUT_DATASET_DIR = os.path.join(os.path.dirname(__file__), "datasets", "crop_classification")

def load_yolo_classes(data_yaml_path):
    with open(data_yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get('names', [])

def get_disease_to_crop_mapping():
    # This is a strict inverse mapping of SUPPORTED_CROPS from disease_config.py
    # If a disease maps to multiple, we pick a primary crop.
    # Note: 'green_mottle' is mapped to cassava and cucumber. We default to cassava.
    return {
        "Canker Rubber Tree": "rubber",
        "Pink Disease": "rubber",
        "Brown BastTree Trunk": "rubber",
        "Healthy Rubber Tree Trunk": "rubber",
        "Healthy Rubber": "rubber",
        "healthy_rubber": "rubber",
        
        "leaf_blast": "rice",
        "leaf_blotch": "rice",
        "narrow_brown": "rice",
        "healthy_rice": "rice",
        "healthy_leaves": "rice",
        
        "Segatoka infected": "banana",
        "healthy_banana": "banana",
        
        "bicho_mineiro": "coffee",
        "brown_spot": "coffee",
        "rust": "coffee",
        "healthy_coffee": "coffee",
        
        "green_mottle": "cassava", # overlapping, defaulting to cassava
        "healthy_cucumber": "cucumber",
        
        "bacterial": "tomato",
        "healthy_tomato": "tomato",
        
        "cassava_mosaic_disease": "cassava",
        "cmd": "cassava",
        "mosaic": "cassava",
        "healthy_cassava": "cassava",
        "healthy_tapioca": "cassava",
        
        # Mapping other YOLO dataset classes that don't have explicit matches in the config
        # 'names' from data.yaml: ['Brown BastTree Trunk', 'Canker Rubber Tree', 'Healthy', 'Healthy Rubber Tree Trunk', 'Pink Disease', 'Segatoka infected', 'bacterial', 'bicho_mineiro', 'brown_spot', 'dry_leaves', 'green_mottle', 'healthy', 'healthy_leaves', 'leaf_blast', 'leaf_blotch', 'narrow_brown', 'objects', 'rhizome', 'rust']
        "Healthy": "unknown_crop",
        "healthy": "unknown_crop",
        "dry_leaves": "unknown_crop",
        "objects": "unknown_crop",
        "rhizome": "ginger" # Ginger/Turmeric
    }

def process_split(split_name, yolo_classes, mapping):
    labels_dir = os.path.join(YOLO_DATASET_DIR, split_name, "labels")
    images_dir = os.path.join(YOLO_DATASET_DIR, split_name, "images")
    
    if not os.path.exists(labels_dir) or not os.path.exists(images_dir):
        print(f"Skipping {split_name} - not found.")
        return
        
    for label_file in os.listdir(labels_dir):
        if not label_file.endswith(".txt"):
            continue
            
        label_path = os.path.join(labels_dir, label_file)
        
        # Read the first label in the file
        with open(label_path, 'r') as f:
            lines = f.readlines()
            if not lines:
                continue
            
            # YOLO format: class_id center_x center_y width height
            try:
                class_id = int(lines[0].split()[0])
            except ValueError:
                continue
                
            if class_id >= len(yolo_classes):
                continue
                
            disease_name = yolo_classes[class_id]
            crop_name = mapping.get(disease_name)
            
            if not crop_name or crop_name == "unknown_crop":
                continue
                
            # Find corresponding image
            image_name = label_file.replace(".txt", ".jpg")
            image_path = os.path.join(images_dir, image_name)
            
            if not os.path.exists(image_path):
                # Try .png or .jpeg
                image_name = label_file.replace(".txt", ".png")
                image_path = os.path.join(images_dir, image_name)
                if not os.path.exists(image_path):
                    image_name = label_file.replace(".txt", ".jpeg")
                    image_path = os.path.join(images_dir, image_name)
                    if not os.path.exists(image_path):
                        continue
                        
            # Copy to destination
            dest_dir = os.path.join(OUTPUT_DATASET_DIR, split_name, crop_name)
            os.makedirs(dest_dir, exist_ok=True)
            
            dest_path = os.path.join(dest_dir, image_name)
            shutil.copy2(image_path, dest_path)

if __name__ == "__main__":
    print("Preparing crop classification dataset from YOLO dataset...")
    data_yaml_path = os.path.join(YOLO_DATASET_DIR, "data.yaml")
    
    if not os.path.exists(data_yaml_path):
        print(f"Error: Could not find {data_yaml_path}")
        sys.exit(1)
        
    yolo_classes = load_yolo_classes(data_yaml_path)
    print(f"Loaded {len(yolo_classes)} YOLO classes.")
    
    mapping = get_disease_to_crop_mapping()
    
    # Create clean output directory
    if os.path.exists(OUTPUT_DATASET_DIR):
        shutil.rmtree(OUTPUT_DATASET_DIR)
        
    process_split("train", yolo_classes, mapping)
    process_split("valid", yolo_classes, mapping)
    process_split("test", yolo_classes, mapping)
    
    print("Dataset preparation complete!")
    print(f"Output saved to: {OUTPUT_DATASET_DIR}")

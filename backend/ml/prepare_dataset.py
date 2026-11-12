import os
import shutil
import yaml
from pathlib import Path
from PIL import Image

def load_data_yaml(yaml_path):
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def clean_class_name(class_id, class_names):
    if class_id < 0 or class_id >= len(class_names):
        return None
        
    name = class_names[class_id].strip()
    
    # Exclude non-leaf/non-disease classes
    exclude = ['objects', 'rhizome', 'Brown BastTree Trunk', 'Healthy Rubber Tree Trunk']
    if name in exclude:
        return None
        
    # Merge healthy classes
    if name.lower() in ['healthy', 'healthy_leaves']:
        return 'healthy'
        
    # Standardize names
    if name == 'Segatoka infected':
        return 'sigatoka'
        
    return name.lower().replace(' ', '_')

def process_split(split_name, img_dir, label_dir, out_dir, class_names):
    if not img_dir.exists() or not label_dir.exists():
        return
        
    print(f"Processing {split_name} split...")
    
    img_files = list(img_dir.glob('*.jpg')) + list(img_dir.glob('*.png')) + list(img_dir.glob('*.jpeg'))
    
    for img_path in img_files:
        label_path = label_dir / f"{img_path.stem}.txt"
        
        if not label_path.exists():
            continue
            
        with open(label_path, 'r') as f:
            lines = f.readlines()
            
        if not lines:
            continue
            
        try:
            img = Image.open(img_path)
            img_w, img_h = img.size
        except Exception as e:
            print(f"Error opening image {img_path}: {e}")
            continue
            
        for i, line in enumerate(lines):
            parts = line.strip().split()
            if len(parts) < 5:
                continue
                
            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])
            
            class_name = clean_class_name(class_id, class_names)
            if not class_name:
                continue
                
            # YOLO format to pixel coordinates
            x_min = int((x_center - w / 2) * img_w)
            y_min = int((y_center - h / 2) * img_h)
            x_max = int((x_center + w / 2) * img_w)
            y_max = int((y_center + h / 2) * img_h)
            
            # Ensure within bounds
            x_min = max(0, x_min)
            y_min = max(0, y_min)
            x_max = min(img_w, x_max)
            y_max = min(img_h, y_max)
            
            if x_max <= x_min or y_max <= y_min:
                continue
                
            class_dir = out_dir / class_name
            class_dir.mkdir(parents=True, exist_ok=True)
            
            crop = img.crop((x_min, y_min, x_max, y_max))
            # Resize slightly to prevent issues with extremely small crops
            if crop.size[0] < 32 or crop.size[1] < 32:
                continue
                
            crop_path = class_dir / f"{img_path.stem}_crop_{i}.jpg"
            crop.save(crop_path, "JPEG", quality=95)

def prepare_dataset(data_yaml_path, output_dir_path):
    print("=" * 50)
    print("Preparing YOLO Classification Dataset")
    print("=" * 50)
    
    yaml_path = Path(data_yaml_path)
    if not yaml_path.exists():
        print(f"Error: {yaml_path} not found.")
        return
        
    data = load_data_yaml(yaml_path)
    base_dir = yaml_path.parent
    class_names = data.get('names', [])
    
    out_base = Path(output_dir_path)
    if out_base.exists():
        shutil.rmtree(out_base)
    
    for split in ['train', 'val', 'test']:
        rel_img_path = data.get(split)
        if not rel_img_path:
            continue
            
        if rel_img_path.startswith('../'):
            img_dir = base_dir / rel_img_path[3:]
        else:
            img_dir = base_dir / rel_img_path
            
        label_dir = img_dir.parent / 'labels'
        out_dir = out_base / split
        
        process_split(split, img_dir, label_dir, out_dir, class_names)
        
    print(f"\nSuccessfully prepared classification dataset at: {out_base}")
    
    # Print stats
    for split in ['train', 'val', 'test']:
        split_dir = out_base / split
        if split_dir.exists():
            total = sum(len(files) for _, _, files in os.walk(split_dir))
            print(f"{split.capitalize()} set: {total} cropped images")
            
            # Print per-class counts for training set
            if split == 'train':
                print("\nTraining class distribution:")
                for class_dir in split_dir.iterdir():
                    if class_dir.is_dir():
                        count = len(list(class_dir.glob('*.jpg')))
                        print(f"  {class_dir.name}: {count}")

if __name__ == "__main__":
    prepare_dataset(r"E:\leaf disease detection.yolov8\data.yaml", r"E:\leaf_disease_yolo_processed")

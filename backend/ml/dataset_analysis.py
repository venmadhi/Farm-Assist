import os
import yaml
from pathlib import Path

def analyze_yolo_detection_dataset(data_yaml_path):
    print("=" * 50)
    print("Dataset Analysis Report")
    print("=" * 50)
    
    if not os.path.exists(data_yaml_path):
        print(f"Error: {data_yaml_path} does not exist.")
        return
        
    with open(data_yaml_path, 'r') as f:
        data = yaml.safe_load(f)
        
    base_dir = Path(data_yaml_path).parent
    
    print(f"Dataset location: {base_dir}")
    print("Dataset type: YOLO Object Detection\n")
    
    classes = data.get('names', [])
    print(f"Number of classes: {len(classes)}")
    print("Classes:")
    for i, cls in enumerate(classes):
        print(f"{i}: {cls}")
    print()
    
    # Count images in splits
    splits = {'train': data.get('train'), 'val': data.get('val'), 'test': data.get('test')}
    
    for split_name, rel_path in splits.items():
        if rel_path:
            # handle relative paths like ../train/images
            if rel_path.startswith('../'):
                split_dir = base_dir / rel_path[3:]
            else:
                split_dir = base_dir / rel_path
                
            if split_dir.exists():
                img_count = len(list(split_dir.glob('*.*')))
                print(f"{split_name.capitalize()} images: {img_count}")
            else:
                print(f"{split_name.capitalize()} images: 0 (Path {split_dir} not found)")
        else:
            print(f"{split_name.capitalize()} images: 0 (Not specified in yaml)")

if __name__ == "__main__":
    analyze_yolo_detection_dataset(r"E:\leaf disease detection.yolov8\data.yaml")

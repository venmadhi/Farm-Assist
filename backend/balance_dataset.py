import os
import shutil
import glob
from collections import defaultdict
import random

def main():
    source_dir = "E:\\leaf disease detection.yolov8"
    dest_dir = "E:\\leaf disease detection.yolov8_balanced"
    
    if not os.path.exists(source_dir):
        print("Source dataset not found.")
        return
        
    # Copy dataset structure
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)
    
    shutil.copy(os.path.join(source_dir, "data.yaml"), dest_dir)
    if os.path.exists(os.path.join(source_dir, "README.roboflow.txt")):
        shutil.copy(os.path.join(source_dir, "README.roboflow.txt"), dest_dir)
    
    # We only balance the 'train' split
    for split in ['train', 'valid', 'test']:
        split_src = os.path.join(source_dir, split)
        split_dst = os.path.join(dest_dir, split)
        
        if not os.path.exists(split_src):
            continue
            
        os.makedirs(os.path.join(split_dst, "images"))
        os.makedirs(os.path.join(split_dst, "labels"))
        
        src_labels = glob.glob(os.path.join(split_src, "labels", "*.txt"))
        
        if split == 'train':
            # Group by main class
            class_groups = defaultdict(list)
            for label_file in src_labels:
                with open(label_file, 'r') as f:
                    content = f.read().strip()
                if content:
                    class_id = content.split()[0]
                    class_groups[class_id].append(label_file)
            
            # Cap at 75 samples per class
            MAX_SAMPLES = 75
            selected_labels = []
            
            for cls_id, files in class_groups.items():
                if len(files) > MAX_SAMPLES:
                    selected_labels.extend(random.sample(files, MAX_SAMPLES))
                else:
                    selected_labels.extend(files)
        else:
            selected_labels = src_labels
            
        # Copy selected files
        for label_file in selected_labels:
            base_name = os.path.splitext(os.path.basename(label_file))[0]
            img_file = os.path.join(split_src, "images", base_name + ".jpg")
            
            if os.path.exists(img_file):
                shutil.copy(label_file, os.path.join(split_dst, "labels", os.path.basename(label_file)))
                shutil.copy(img_file, os.path.join(split_dst, "images", os.path.basename(img_file)))
    
    print(f"Balanced dataset created at {dest_dir}")
    
if __name__ == "__main__":
    main()

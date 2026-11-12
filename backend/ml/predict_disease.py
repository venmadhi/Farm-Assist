import os
import argparse
from pathlib import Path
from ultralytics import YOLO

# A simple mapping of supported crops in Kerala context
# This helps with the cross-crop misclassification logic
SUPPORTED_CROPS = {
    'banana': ['sigatoka'],
    'rice': ['leaf_blast', 'narrow_brown', 'leaf_blotch'],
    'rubber': ['canker_rubber_tree', 'pink_disease'],
    # the dataset lacks explicit crop associations for some classes, 
    # but we can try to infer based on knowledge
    # For now, we will just have a list of all diseases we handle
}

def predict_single_image(model_path, image_path, conf_threshold=0.60):
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return
        
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    print(f"Loading model: {model_path}")
    model = YOLO(model_path)
    
    print(f"Analyzing image: {image_path}")
    results = model(image_path)
    
    result = results[0]
    names = result.names
    probs = result.probs
    
    top5_indices = probs.top5
    top5_conf = probs.top5conf
    
    best_idx = top5_indices[0]
    best_conf = top5_conf[0].item()
    best_class = names[best_idx]
    
    print("\n" + "=" * 50)
    print("Prediction Results")
    print("=" * 50)
    
    if best_conf < conf_threshold:
        print(f"Top Prediction: {best_class} ({best_conf:.2f} confidence)")
        print("\n⚠️  Unable to confidently identify the disease.")
        print("Please upload a clearer image of the affected leaf, or the image may contain an unsupported crop/object.")
    elif best_class == "healthy":
        print(f"Status: Healthy Leaf")
        print(f"Confidence: {best_conf:.2f}")
    else:
        print(f"Predicted Disease: {best_class.replace('_', ' ').title()}")
        print(f"Confidence: {best_conf:.2f}")
        
    print("\nTop 3 Predictions:")
    for i in range(min(3, len(top5_indices))):
        idx = top5_indices[i]
        conf = top5_conf[i].item()
        print(f"{i+1}. {names[idx].replace('_', ' ').title()} - {conf:.2f}")
        
    print("=" * 50)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict crop disease from leaf image")
    parser.add_argument("--image", type=str, required=True, help="Path to the leaf image")
    parser.add_argument("--model", type=str, default=r"E:\leaf_disease_yolo_training\models\yolo11_disease_best.pt", help="Path to trained YOLO model")
    parser.add_argument("--conf", type=float, default=0.60, help="Confidence threshold")
    
    args = parser.parse_args()
    predict_single_image(args.model, args.image, args.conf)

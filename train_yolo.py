from ultralytics import YOLO
import os

def main():
    # Load pre-trained nano model for faster CPU transfer learning
    model = YOLO("yolov8n.pt") 
    
    print("Starting YOLO object detection training...")
    # Train the model
    results = model.train(
        data=r"E:\leaf disease detection.yolov8\data.yaml",
        epochs=10,        # Increased to 10 as approved
        imgsz=320,        # Reduced for CPU speed
        batch=8,          # Lower batch size
        project=r"backend\app\ml\weights",
        name="leaf_disease",
        exist_ok=True     # Overwrite if exists
    )
    
    print("Training complete. Results:")
    if hasattr(results, 'results_dict'):
        print(results.results_dict)
    
if __name__ == "__main__":
    main()

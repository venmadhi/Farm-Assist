import os
import shutil
import json
import pandas as pd
from ultralytics import YOLO

def main():
    print("Starting YOLO Object Detection Training with image weights...")
    
    # Load the base object detection model
    model = YOLO("yolo11n.pt")
    
    # Train the model for more epochs with early stopping (patience)
    # Using balanced dataset to balance class frequencies
    model.train(
        data="E:\\leaf disease detection.yolov8 database\\data.yaml", 
        epochs=100, 
        patience=20,
        imgsz=320,
        workers=0,
        batch=16,
        project="runs/detect",
        name="disease_model",
        exist_ok=True,
        device=0
    )
    
    source_weights = os.path.join("runs", "detect", "disease_model", "weights", "best.pt")
    dest_weights = os.path.join("app", "ml", "weights", "leaf_disease_best.pt")
    
    if os.path.exists(source_weights):
        os.makedirs(os.path.dirname(dest_weights), exist_ok=True)
        shutil.copy2(source_weights, dest_weights)
        print(f"Training complete! Best weights automatically deployed to: {dest_weights}")
    else:
        print("Training complete, but could not find the best weights to copy.")

    # Extract metrics from results.csv and save to disease_metrics.json
    results_csv = os.path.join("runs", "detect", "disease_model", "results.csv")
    if os.path.exists(results_csv):
        df = pd.read_csv(results_csv)
        df.columns = df.columns.str.strip() # Strip whitespace from column names
        
        # Find the row with best mAP50-95
        best_row = df.loc[df['metrics/mAP50-95(B)'].idxmax()]
        
        metrics = {
            "precision": float(best_row.get("metrics/precision(B)", 0.0)),
            "recall": float(best_row.get("metrics/recall(B)", 0.0)),
            "map50": float(best_row.get("metrics/mAP50(B)", 0.0)),
            "map50_95": float(best_row.get("metrics/mAP50-95(B)", 0.0)),
            "training_epochs": int(best_row.get("epoch", 0)) + 1
        }
        
        metrics_path = os.path.join("app", "ml", "models", "disease_metrics.json")
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=4)
        print(f"Metrics saved to {metrics_path}")
    else:
        print("Could not find results.csv to extract metrics.")

if __name__ == "__main__":
    main()

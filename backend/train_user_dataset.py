from ultralytics import YOLO
import os

print("Starting YOLO Detection Model Training on the new Dataset...")

# Initialize YOLO detection model
model = YOLO("yolo11n.pt") # Pretrained weights for detection

data_yaml = r"E:\leaf disease detection.yolov8\data.yaml"
project_dir = r"E:\farm assistant project\Farm-Assist-main\backend\runs\detect_new"

print(f"Training on: {data_yaml}")

results = model.train(
    data=data_yaml,
    epochs=100,
    imgsz=640,
    batch=16,
    patience=15,
    project=project_dir,
    name="disease_model",
    exist_ok=True,
    pretrained=True
)

print("Training Completed.")

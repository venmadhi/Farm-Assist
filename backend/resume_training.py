from ultralytics import YOLO
import torch

print("Resuming YOLO Classification Model Training...")
model_cls = YOLO(r"e:\farm assistant project\Farm-Assist-main\backend\runs\classify\runs\classify\disease_model\weights\last.pt")
model_cls.train(resume=True)
print("Classification Model Training Completed.")

print("Resuming YOLO Detection Model Training...")
model_det = YOLO(r"e:\farm assistant project\Farm-Assist-main\backend\runs\detect\runs\detect\disease_model\weights\last.pt")
model_det.train(resume=True)
print("Detection Model Training Completed.")

print("All YOLO models successfully resumed and trained to completion.")

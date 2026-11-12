from ultralytics import YOLO

print("Resuming YOLO Detection Model Training (300 Epoch Run)...")
model = YOLO(r"E:\farm assistant project\Farm-Assist-main\runs\detect\backend\app\ml\weights\leaf_disease_fast\weights\last.pt")
model.train(resume=True)
print("Training Completed.")

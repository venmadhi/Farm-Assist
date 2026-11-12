from ultralytics import YOLO

# Load the NEW trained object detection model
model = YOLO('runs/detect/disease_model/weights/best.pt')

# Load the test image
img_path = 'static/uploads/005a22a1-6c21-40be-a521-3c69a4a9cc54.jpg'
print(f'Running inference on {img_path}...')

# Run inference
results = model(img_path, verbose=False)

# Print results
for r in results:
    if r.probs is not None:
        top5_probs = r.probs.top5
        top5_confs = r.probs.top5conf
        print('Raw Prediction Scores:')
        for i, (idx, conf) in enumerate(zip(top5_probs, top5_confs)):
            print(f'{i+1}. Class: {r.names[idx]}, Confidence: {conf:.4f}')
    elif hasattr(r, "boxes") and r.boxes is not None and len(r.boxes) > 0:
        print('Raw Object Detection Boxes:')
        for i, box in enumerate(r.boxes):
            cls_idx = int(box.cls[0])
            conf = float(box.conf[0])
            print(f'{i+1}. Class: {r.names[cls_idx]}, Confidence: {conf:.4f}')
    else:
        print('No predictions found.')

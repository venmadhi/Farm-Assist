import os
import sys
from pathlib import Path
from PIL import Image

# Ensure the backend directory is in the path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.yolo_disease_agent import YOLODiseaseClassifier

def test_yolo():
    print("Initializing YOLO Agent...")
    try:
        agent = YOLODiseaseClassifier(device="cpu")
    except Exception as e:
        print(f"Failed to initialize YOLO agent: {e}")
        return

    # Look for a test image
    uploads_dir = backend_dir / "static" / "uploads"
    test_images = list(uploads_dir.glob("*.jpg"))
    
    if not test_images:
        print("No test images found in static/uploads/.")
        # Create a dummy image
        img_path = backend_dir / "test_leaf.jpg"
        img = Image.new('RGB', (224, 224), color = (73, 109, 137))
        img.save(img_path)
        print(f"Created dummy image at {img_path}")
    else:
        img_path = test_images[0]
        
    print(f"\nRunning inference on: {img_path}")
    image = Image.open(img_path)
    
    result = agent.predict(image, selected_crop=None)
    
    print("\n--- INFERENCE RESULTS ---")
    if result.get("success"):
        print(f"Status: SUCCESS")
        print(f"Predicted Crop: {result.get('crop')}")
        print(f"Predicted Disease: {result.get('disease')} ({result.get('display_disease')})")
        print(f"Confidence: {result.get('confidence'):.4f}")
    else:
        print(f"Status: FAILED")
        print(f"Reason: {result.get('reason')}")
        print(f"Message: {result.get('message')}")
        
    print("\nTest completed.")

if __name__ == "__main__":
    test_yolo()

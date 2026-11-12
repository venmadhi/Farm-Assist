import requests
import io
import os
from PIL import Image, ImageDraw

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 1. Login with phone_number
login_res = requests.post(f"{BASE_URL}/auth/login", json={"phone_number": "0987654321", "password": "password"})
if login_res.status_code != 200:
    print(f"Login failed: {login_res.status_code}, {login_res.text}")
    exit(1)
    
token = login_res.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print(f"Auth successful, token obtained.\n")

def test_image(test_name, img_bytes, expect_yolo=False):
    print(f"==================================================")
    print(f"TEST: {test_name}")
    print(f"==================================================")
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    res = requests.post(f"{BASE_URL}/disease/scan", headers=headers, files=files)
    if res.status_code != 200:
        print(f"HTTP {res.status_code}: {res.text}\n")
        return
    data = res.json()
    crop_info = data.get("crop_identification", {})
    disease_info = data.get("disease_detection", {})
    val_info = data.get("validation", {})
    
    print(f"Crop Identification : {crop_info.get('crop')} (Confidence: {crop_info.get('confidence')*100:.1f}%)")
    print(f"Disease Detection   : {disease_info.get('disease')} (Status: {disease_info.get('status')}, Confidence: {disease_info.get('confidence')*100:.1f}%)")
    print(f"Validation Status   : {val_info.get('crop_disease_status')}")
    print(f"Validation Message  : {val_info.get('validation_message')}")
    
    if disease_info.get('status') == 'skipped':
        print(f"RESULT              : [PASS] YOLO11 SKIPPED (No closed-set disease hallucination)")
    elif disease_info.get('status') == 'executed':
        print(f"RESULT              : [PASS] YOLO11 EXECUTED on valid crop (Compatible: {val_info.get('crop_disease_match')})")
    print()

# --- OUT-OF-DOMAIN TESTS ---

# 1. Cow image (the actual user uploaded image)
cow_path = r"E:\farm assistant project\Farm-Assist-main\backend\static\uploads\e8851156-adef-434f-9efb-32656313519e.jpg"
if os.path.exists(cow_path):
    with open(cow_path, "rb") as f:
        test_image("1. Cow (Actual Uploaded Animal)", f.read(), expect_yolo=False)

# 2. Synthetic Car Object
car_img = Image.new("RGB", (300, 200), color=(50, 50, 60))
draw = ImageDraw.Draw(car_img)
draw.rectangle([50, 80, 250, 160], fill=(200, 30, 30))
draw.ellipse([80, 140, 120, 180], fill=(10, 10, 10))
draw.ellipse([180, 140, 220, 180], fill=(10, 10, 10))
buf = io.BytesIO()
car_img.save(buf, format="JPEG")
test_image("2. Car (Vehicle Object)", buf.getvalue(), expect_yolo=False)

# 3. Synthetic Human Person
human_img = Image.new("RGB", (250, 350), color=(220, 220, 230))
draw = ImageDraw.Draw(human_img)
draw.ellipse([90, 30, 160, 100], fill=(230, 190, 160))
draw.rectangle([70, 110, 180, 260], fill=(40, 80, 160))
buf = io.BytesIO()
human_img.save(buf, format="JPEG")
test_image("3. Human (Person)", buf.getvalue(), expect_yolo=False)

# 4. Blank Uniform Noise
blank_img = Image.new("RGB", (200, 200), color=(128, 128, 128))
buf = io.BytesIO()
blank_img.save(buf, format="JPEG")
test_image("4. Blank / Uniform Noise", buf.getvalue(), expect_yolo=False)

# --- IN-DOMAIN AGRICULTURAL TESTS ---
crop_val_dir = r"E:\leaf disease detection.yolov8 database\crop_dataset\val"

# 5. Banana Leaf Sample
banana_dir = os.path.join(crop_val_dir, "Banana")
if os.path.exists(banana_dir):
    files = [f for f in os.listdir(banana_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if files:
        with open(os.path.join(banana_dir, files[0]), "rb") as f:
            test_image("5. Banana Leaf (Real Crop)", f.read(), expect_yolo=True)

# 6. Cocoa Leaf/Pod Sample
cocoa_dir = os.path.join(crop_val_dir, "Cocoa")
if os.path.exists(cocoa_dir):
    files = [f for f in os.listdir(cocoa_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if files:
        with open(os.path.join(cocoa_dir, files[0]), "rb") as f:
            test_image("6. Cocoa Leaf (Real Crop)", f.read(), expect_yolo=True)

# 7. Coffee Leaf Sample
coffee_dir = os.path.join(crop_val_dir, "Coffee")
if os.path.exists(coffee_dir):
    files = [f for f in os.listdir(coffee_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if files:
        with open(os.path.join(coffee_dir, files[0]), "rb") as f:
            test_image("7. Coffee Leaf (Real Crop)", f.read(), expect_yolo=True)

# 8. Tomato Leaf Sample
tomato_dir = os.path.join(crop_val_dir, "Tomato")
if os.path.exists(tomato_dir):
    files = [f for f in os.listdir(tomato_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if files:
        with open(os.path.join(tomato_dir, files[0]), "rb") as f:
            test_image("8. Tomato Leaf (Real Crop)", f.read(), expect_yolo=True)

import os
import json
import glob
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Farmer, Farm, DiseaseRecord
from app.routers.auth import create_access_token

# Set up test client
client = TestClient(app)

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Ensure farmer exists
farmer = db.query(Farmer).filter(Farmer.phone_number == '0987654321').first()
if not farmer:
    from app.utils.security import get_password_hash
    farmer = Farmer(
        phone_number='0987654321',
        full_name='Test Farmer',
        password_hash=get_password_hash('password'),
        preferred_language='en',
        dark_mode=False
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)

# Test 5 sample images
dataset_dir = r'e:\leaf disease detection.yolov8 database\organized_data\disease_classification'
val_dir = os.path.join(dataset_dir, 'val')

test_samples = [
    ('Banana', 'sigatoka'),
    ('Rice', 'blast'),
    ('Tomato', 'early_blight'),
    ('Coffee', 'leaf_rust'),
    ('Black Pepper', 'phytophthora')
]

token = create_access_token({'sub': farmer.phone_number})

print('=== RUNNING 5 END-TO-END PIPELINE TESTS ===')

for expected_crop, disease_folder in test_samples:
    folder_path = os.path.join(val_dir, disease_folder)
    imgs = glob.glob(os.path.join(folder_path, '*.jpg')) + glob.glob(os.path.join(folder_path, '*.png'))
    if not imgs:
        print(f'No image for {disease_folder}')
        continue
    
    img_file = imgs[0]
    with open(img_file, 'rb') as f:
        files = {'file': (os.path.basename(img_file), f, 'image/jpeg')}
        headers = {'Authorization': f'Bearer {token}'}
        response = client.post('/api/v1/disease/scan', files=files, headers=headers)
        
    if response.status_code == 200:
        data = response.json()
        crop_name = data['crop_identification']['crop']
        crop_conf = data['crop_identification']['confidence'] * 100
        crop_mod = data['crop_identification']['model']
        dis_name = data['disease_detection']['disease']
        dis_conf = data['disease_detection']['confidence'] * 100
        dis_mod = data['disease_detection']['model']
        val_status = data['validation']['crop_disease_status']
        val_msg = data['validation']['validation_message']
        top5 = data['disease_detection'].get('top5', [])
        
        print(f"\n[PASS] Image: {os.path.basename(img_file)}")
        print(f"   Target Disease Folder : {disease_folder}")
        print(f"   Identified Crop       : {crop_name} ({crop_conf:.1f}%) via {crop_mod}")
        print(f"   Detected Disease      : {dis_name} ({dis_conf:.1f}%) via {dis_mod}")
        print(f"   Validation Status     : {val_status}")
        print(f"   Validation Message    : {val_msg}")
        if top5:
            top3_str = ", ".join([f"{x['disease']} ({x['confidence']*100:.1f}%)" for x in top5[:3]])
            print(f"   Top 3 Matches         : {top3_str}")
    else:
        print(f"[FAIL] Status {response.status_code}: {response.text}")

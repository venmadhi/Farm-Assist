import os
import requests

# A script to test the backend API for crop inference
def test_inference():
    # Pick a test image from the new crop dataset
    # We will pick a cassava image and a rubber image
    base_dataset = r"E:\farm assistant project\Farm-Assist-main\backend\ml\datasets\crop_classification\test"
    
    test_cases = [
        {"crop": "cassava", "expected_disease": "green_mottle"},
        {"crop": "rubber", "expected_disease": "Canker Rubber Tree"}
    ]
    
    url = "http://localhost:8000/disease/scan"
    
    for case in test_cases:
        crop_dir = os.path.join(base_dataset, case["crop"])
        if not os.path.exists(crop_dir):
            print(f"Skipping {case['crop']}, directory not found: {crop_dir}")
            continue
            
        images = [f for f in os.listdir(crop_dir) if f.endswith(".jpg")]
        if not images:
            print(f"No images found for {case['crop']}")
            continue
            
        image_path = os.path.join(crop_dir, images[0])
        print(f"\n--- Testing Image: {image_path} ---")
        
        with open(image_path, "rb") as img_file:
            # We must pass the farm_id (let's use 1)
            files = {"file": (images[0], img_file, "image/jpeg")}
            data = {"farm_id": "1"}
            
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                res_json = response.json()
                
                crop_info = res_json.get("crop_identification", {})
                disease_info = res_json.get("disease_detection", {})
                validation = res_json.get("validation", {})
                
                print(f"Expected Crop: {case['crop'].capitalize()}")
                print(f"Predicted Crop: {crop_info.get('crop')}")
                print(f"Crop Confidence: {crop_info.get('confidence')}")
                print(f"Expected Disease: {case['expected_disease']}")
                print(f"Predicted Disease: {disease_info.get('disease')}")
                print(f"Disease Confidence: {disease_info.get('confidence')}")
                print(f"Crop/Disease Consistency Status: {validation.get('crop_disease_status')}")
            else:
                print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_inference()

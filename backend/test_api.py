import requests

# Test the FastAPI endpoint
url = "http://localhost:8000/api/v1/disease/scan"

# Assuming the backend is running...
try:
    with open("test_leaf.jpg", "rb") as f:
        files = {"file": f}
        print(f"Sending POST to {url}...")
        response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:", response.json())
        except Exception:
            print("Response Text:", response.text)
except FileNotFoundError:
    print("test_leaf.jpg not found. Please run test_yolo.py first to generate a dummy image.")
except requests.exceptions.ConnectionError:
    print("Backend is not running. Please start it using uvicorn main:app --port 8000")

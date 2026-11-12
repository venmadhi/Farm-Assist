import requests
from io import BytesIO
from PIL import Image

# Create a dummy image
img = Image.new('RGB', (224, 224), color = (73, 109, 137))
img_io = BytesIO()
img.save(img_io, 'JPEG')
img_io.seek(0)

url = "http://localhost:8000/api/v1/disease/scan"
login_url = "http://localhost:8000/api/v1/auth/login"

try:
    # Login to get token
    login_data = {"phone_number": "0987654321", "password": "password"}
    login_resp = requests.post(login_url, json=login_data)
    token = login_resp.json().get("access_token")
    
    headers = {"Authorization": f"Bearer {token}"}
    files = {'file': ('dummy.jpg', img_io, 'image/jpeg')}
    data = {'crop': 'Tomato'}
    print(f"Sending POST to {url}...")
    response = requests.post(url, files=files, data=data, headers=headers)
    print("Status:", response.status_code)
    print("Response:", response.text)
except requests.exceptions.RequestException as e:
    print("Request failed:", e)

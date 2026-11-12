import requests

token_url = "http://localhost:8000/api/v1/auth/login"
market_url = "http://localhost:8000/api/v1/market/trends"

print("1. Logging in to get token...")
try:
    resp = requests.post(token_url, json={"phone_number":"0987654321", "password":"password"})
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print("   Success!")
except Exception as e:
    print("   Failed to login:", e)
    exit(1)

print("\n2. Fetching Market Trends for Banana (Palakkad)...")
headers = {"Authorization": f"Bearer {token}"}
params = {"crop": "banana", "district": "Palakkad"}

resp = requests.get(market_url, headers=headers, params=params)
print(f"   Status Code: {resp.status_code}")
try:
    print("   Response:", resp.json())
except:
    print("   Response:", resp.text)

print("\n3. Fetching Market Trends for Unsupported Crop (Rubber)...")
params = {"crop": "rubber", "district": "Palakkad"}
resp = requests.get(market_url, headers=headers, params=params)
print(f"   Status Code: {resp.status_code}")
try:
    print("   Response:", resp.json())
except:
    print("   Response:", resp.text)

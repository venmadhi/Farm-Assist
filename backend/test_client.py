from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Login or Register
headers = {}
print("--- 1. REGISTER USER ---")
try:
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Test Farmer",
        "phone_number": "0123456789",
        "password": "password",
        "location_district": "Palakkad",
        "soil_type": "Laterite",
        "land_area_acres": 1.5
    })
    print("Register Status:", response.status_code)
    # If already registered, let's login
    if response.status_code == 400 or "already registered" in response.text:
        print("User already registered. Proceeding to login...")
except Exception as e:
    print("Register failed:", e)

print("\n--- 2. LOGIN USER ---")
response = client.post("/api/v1/auth/login", json={
    "phone_number": "0123456789",
    "password": "password"
})
print("Login Status:", response.status_code)
token = response.json().get("access_token")
headers["Authorization"] = f"Bearer {token}"

# 2. Query Crop Recommendation
print("\n--- 3. TEST CROP RECOMMENDATION ---")
crop_payload = {
    "farm_id": 1,  # Note: our router dynamically handles this anyway!
    "nitrogen": 75.0,
    "phosphorus": 45.0,
    "potassium": 55.0,
    "ph": 6.5,
    "organic_carbon": 0.6,
    "boron": 0.25,
    "iron": 4.5,
    "zinc": 0.65,
    "temperature": 28.0,
    "humidity": 75.0,
    "rainfall": 1500.0,
    "season": "Kharif"
}
response = client.post("/api/v1/crop/recommend", json=crop_payload, headers=headers)
print("Crop Recommend Status:", response.status_code)
if response.status_code == 200:
    preds = response.json().get("predictions", [])
    print("Predictions count:", len(preds))
    if preds:
        print("Top recommended crop:", preds[0]["crop_name"])
        print("Confidence:", preds[0]["confidence_score"])
        print("Expected Yield:", preds[0]["expected_yield"])
        print("Estimated Profit:", preds[0]["estimated_profit"])
        print("SHAP contributions:", preds[0]["shap_contributions"])
else:
    print("Error response:", response.text)

# 2.5. Log live weather to database to seed WeatherHistory
print("\n--- 3.5. LOG LIVE WEATHER FOR FARM ---")
weather_response = client.get("/api/v1/profile/weather", headers=headers)
print("Weather API Status:", weather_response.status_code)

# 3. Query Fertilizer calculation
print("\n--- 4. TEST FERTILIZER CALCULATION ---")
fert_payload = {
    "farm_id": 1,
    "crop_name": "banana",
    "nitrogen": 60.0,
    "phosphorus": 35.0,
    "potassium": 45.0,
    "ph": 6.2
}
response = client.post("/api/v1/fertilizer/calculate", json=fert_payload, headers=headers)
print("Fertilizer Calculate Status:", response.status_code)
if response.status_code == 200:
    res = response.json()
    print("N Status:", res.get("n_status"))
    print("P Status:", res.get("p_status"))
    print("K Status:", res.get("k_status"))
    print("Estimated Cost:", res.get("estimated_cost"))
    print("Schedule count:", len(res.get("fertilizer_schedule", [])))
else:
    print("Error response:", response.text)

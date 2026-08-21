import sys
import os
import unittest
import datetime
from fastapi.testclient import TestClient

# Adjust path to import backend app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import engine, Base, get_db
from app.models import Farmer, Farm, CropCycle, ModelVersion, CropHistory
from sqlalchemy.orm import Session

class TestFarmingCycles(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        Base.metadata.create_all(bind=engine)
        
        # Clear existing test data
        self.db = Session(bind=engine)
        self.db.query(CropCycle).delete()
        self.db.query(ModelVersion).delete()
        self.db.query(CropHistory).delete()
        self.db.query(Farmer).filter(Farmer.phone_number == "1234567890").delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_farming_cycle_workflow(self):
        # 1. Register
        reg_resp = self.client.post("/api/v1/auth/register", json={
            "full_name": "Test Farmer",
            "phone_number": "1234567890",
            "password": "password",
            "location_district": "Palakkad",
            "soil_type": "Laterite",
            "land_area_acres": 1.5,
            "preferred_language": "english"
        })
        self.assertEqual(reg_resp.status_code, 200)
        
        # 2. Login
        login_resp = self.client.post("/api/v1/auth/login", json={
            "phone_number": "1234567890",
            "password": "password"
        })
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Check digital twin empty state
        twin_resp = self.client.get("/api/v1/profile/twin", headers=headers)
        self.assertEqual(twin_resp.status_code, 200)
        twin_data = twin_resp.json()
        self.assertEqual(twin_data["digital_twin_metrics"]["expected_yield_kg"], 0.0)
        self.assertEqual(twin_data["digital_twin_metrics"]["expected_profit_inr"], 0.0)
        self.assertEqual(len(twin_data["crop_history"]), 0)
        self.assertEqual(len(twin_data["active_cycles"]), 0)
        
        # 4. Start crop cycle
        start_resp = self.client.post("/api/v1/profile/crop-cycle", headers=headers, json={
            "crop_name": "banana",
            "season": "Kharif",
            "year": 2026,
            "area_acres": 1.5,
            "expected_yield": 1200.0,
            "expected_profit": 35000.0,
            "expected_revenue": 50000.0
        })
        self.assertEqual(start_resp.status_code, 200)
        cycle_id = start_resp.json()["id"]
        
        # Verify active cycle shows in digital twin
        twin_resp = self.client.get("/api/v1/profile/twin", headers=headers)
        twin_data = twin_resp.json()
        self.assertEqual(len(twin_data["active_cycles"]), 1)
        self.assertEqual(twin_data["digital_twin_metrics"]["expected_yield_kg"], 1200.0)
        self.assertEqual(twin_data["digital_twin_metrics"]["expected_profit_inr"], 35000.0)
        
        # 5. Harvest crop cycle
        harvest_resp = self.client.post(f"/api/v1/profile/crop-cycle/{cycle_id}/harvest", headers=headers, json={
            "actual_yield": 1100.0,
            "actual_selling_price": 45.0,
            "cultivation_cost": 12000.0,
            "fertilizer_used": "Organic manure",
            "disease_incidence": "None"
        })
        self.assertEqual(harvest_resp.status_code, 200)
        harvested_cycle = harvest_resp.json()
        
        self.assertEqual(harvested_cycle["status"], "HARVESTED")
        self.assertEqual(harvested_cycle["actual_yield"], 1100.0)
        self.assertEqual(harvested_cycle["actual_revenue"], 1100.0 * 45.0)
        self.assertEqual(harvested_cycle["actual_profit"], (1100.0 * 45.0) - 12000.0)
        
        # Verify cycle moved from active to completed
        twin_resp = self.client.get("/api/v1/profile/twin", headers=headers)
        twin_data = twin_resp.json()
        self.assertEqual(len(twin_data["active_cycles"]), 0)
        self.assertEqual(len(twin_data["crop_history"]), 1)
        self.assertEqual(twin_data["digital_twin_metrics"]["expected_yield_kg"], 0.0)
        
        # Verify manual retraining check
        retrain_resp = self.client.post("/api/v1/profile/model-retrain", headers=headers)
        self.assertEqual(retrain_resp.status_code, 200)
        self.assertTrue(retrain_resp.json()["triggered"])
        self.assertIn("Successfully retrained", retrain_resp.json()["message"])

if __name__ == "__main__":
    unittest.main()

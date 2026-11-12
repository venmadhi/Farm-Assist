from app.database import SessionLocal, engine, Base
from app.models import Farmer, Farm, CropCycle
from app.ml.crop_agent import crop_agent
import datetime

# Create all tables first
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Setup test data
farmer = db.query(Farmer).first()
if not farmer:
    farmer = Farmer(full_name="Test Farmer", phone_number="1234567890", password_hash="hash")
    db.add(farmer)
    db.commit()

farm = db.query(Farm).filter(Farm.farmer_id == farmer.id).first()
if not farm:
    farm = Farm(farmer_id=farmer.id, farm_name="Rotation Test Farm")
    db.add(farm)
    db.commit()
    
# Remove old crop cycles for this farm
db.query(CropCycle).filter(CropCycle.farm_id == farm.id).delete()
db.commit()

# Predict without history
print("=== BEFORE ROTATION (NO HISTORY) ===")
res_before = crop_agent.recommend(
    db=db, farm_id=farm.id, 
    n=80, p=48, k=48, ph=6.2, 
    organic_carbon=0.8, boron=0.2, iron=4.5, zinc=0.6,
    temp=28, humidity=82, rainfall=2000, season="Kharif"
)
for r in res_before:
    print(f"{r['crop_name']}: {r['confidence_score']} | Reason: {r['reason']}")

print("\n=== ADDING HISTORY (PADDY JUST HARVESTED) ===")
# Add paddy harvest history
cycle = CropCycle(
    farm_id=farm.id,
    crop_name="paddy",
    season="Kharif",
    year=2025,
    start_date=datetime.datetime.now() - datetime.timedelta(days=120),
    harvest_date=datetime.datetime.now(),
    status="HARVESTED",
    expected_yield=2000,
    expected_profit=50000,
    expected_revenue=60000,
    soil_nitrogen=80,
    soil_phosphorus=48,
    soil_potassium=48,
    soil_ph=6.2
)
db.add(cycle)
db.commit()

print("\n=== AFTER ROTATION ===")
res_after = crop_agent.recommend(
    db=db, farm_id=farm.id, 
    n=80, p=48, k=48, ph=6.2, 
    organic_carbon=0.8, boron=0.2, iron=4.5, zinc=0.6,
    temp=28, humidity=82, rainfall=2000, season="Kharif"
)
for r in res_after:
    print(f"{r['crop_name']}: {r['confidence_score']} | Reason: {r['reason']}")

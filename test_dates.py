import sys
sys.path.append('backend')
from app.database import SessionLocal
from app.models import CropCycle, Farmer, Farm
from app.schemas import CropHistoryCreate
from datetime import date
from app.routers.profile import add_crop_history

db = SessionLocal()
farmer = db.query(Farmer).first()
farm = db.query(Farm).first()

# submit harvest
history_in = CropHistoryCreate(crop_name='Rice', yield_kg=500, season='Kharif', year=2026, start_date=date(2026, 9, 15), end_date=date(2026, 9, 20), revenue=1000)
try:
    res = add_crop_history(history_in, current_farmer=farmer, db=db)
    print("Harvest Submitted!")
except Exception as e:
    print(f"Error submitting harvest: {e}")

# verify
cycle = db.query(CropCycle).filter(CropCycle.farm_id==farm.id, CropCycle.crop_name=='Rice', CropCycle.season=='Kharif', CropCycle.year==2026).first()
if cycle:
    print('\n--- CYCLE DATES ---')
    print(f'Start: {cycle.start_date}')
    print(f'Harvest: {cycle.harvest_date}')
    print(f'Status: {cycle.status}')
else:
    print("Cycle not found")

count = db.query(CropCycle).filter(CropCycle.crop_name=='Rice').count()
print(f'Total Rice Cycles: {count}')

db.close()

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.ml.crop_agent import crop_agent
from app.models import Base

engine = create_engine('sqlite:///backend/agrigenie.db')
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Test recommendation
results = crop_agent.recommend(
    db=db, farm_id=1,
    n=100, p=50, k=100, ph=6.5,
    organic_carbon=1.5, boron=0.5, iron=5.0, zinc=1.0,
    temp=28, humidity=75, rainfall=1500, season='Kharif'
)

for r in results:
    print(f"{r['crop_name']}: {r['confidence_score']:.2%} | Reason: {r['reason']}")

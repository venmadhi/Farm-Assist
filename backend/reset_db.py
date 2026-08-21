import sys
import os
from sqlalchemy import text

# Adjust path to import backend app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import engine, Base
from app.models import Farmer, Farm, SoilTest, CropHistory, WeatherHistory, DiseaseRecord, FertilizerHistory, CropPrediction, YieldPrediction, Notification, RecommendationHistory, CropCycle, ModelVersion

def reset_database():
    print("WARNING: Re-creating MySQL tables to match new 12-table schema...")
    
    # 1. Drop all tables
    try:
        # Disable foreign key checks for clean drop in MySQL
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            conn.commit()
            
        Base.metadata.drop_all(bind=engine)
        print("Dropped all existing tables successfully.")
    except Exception as e:
        print(f"Error dropping tables: {e}")
        
    # 2. Re-create all tables with correct schemas
    try:
        Base.metadata.create_all(bind=engine)
        print("Re-created all tables with updated SQLAlchemy schemas successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        
    # 3. Re-enable foreign key checks
    try:
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            conn.commit()
    except Exception as e:
        print(f"Error restoring foreign key checks: {e}")

if __name__ == "__main__":
    reset_database()

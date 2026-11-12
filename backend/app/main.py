import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import engine, Base
from .routers import auth, profile, crop, disease, fertilizer, chatbot, market, notifications

# Initialize database tables on startup
# Initialize database tables on startup
try:
    Base.metadata.create_all(bind=engine)
    from sqlalchemy import text
    with engine.connect() as conn:
        # 1. Migrate farmers
        for col, col_type in [("preferred_language", "VARCHAR(50) DEFAULT 'english'"), ("dark_mode", "BOOLEAN DEFAULT FALSE")]:
            try:
                conn.execute(text(f"SELECT {col} FROM farmers LIMIT 1;"))
            except Exception:
                try:
                    conn.execute(text(f"ALTER TABLE farmers ADD COLUMN {col} {col_type};"))
                    conn.commit()
                    print(f"Migrated: added {col} to farmers table.")
                except Exception as em:
                    print(f"Migration farmers.{col} failed: {em}")

        # 2. Migrate crop_history
        for col, col_type in [
            ("farm_id", "INT NOT NULL DEFAULT 1"),
            ("weather_summary", "VARCHAR(255) NULL"),
            ("disease_incidence", "VARCHAR(255) NULL"),
            ("fertilizer_used", "VARCHAR(255) NULL"),
            ("market_price", "FLOAT NULL")
        ]:
            try:
                conn.execute(text(f"SELECT {col} FROM crop_history LIMIT 1;"))
            except Exception:
                try:
                    conn.execute(text(f"ALTER TABLE crop_history ADD COLUMN {col} {col_type};"))
                    conn.commit()
                    print(f"Migrated: added {col} to crop_history table.")
                except Exception as em:
                    print(f"Migration crop_history.{col} failed: {em}")

        # 3. Migrate fertilizer_history
        for col, col_type in [
            ("recommended_type", "VARCHAR(255) NULL"),
            ("dosage_g_sqm", "FLOAT NULL"),
            ("estimated_cost", "FLOAT NULL")
        ]:
            try:
                conn.execute(text(f"SELECT {col} FROM fertilizer_history LIMIT 1;"))
            except Exception:
                try:
                    conn.execute(text(f"ALTER TABLE fertilizer_history ADD COLUMN {col} {col_type};"))
                    conn.commit()
                    print(f"Migrated: added {col} to fertilizer_history table.")
                except Exception as em:
                    print(f"Migration fertilizer_history.{col} failed: {em}")

        # 4. Migrate disease_records
        for col, col_type in [
            ("recovery_time_days", "INT NOT NULL DEFAULT 14"),
            ("crop", "VARCHAR(100) DEFAULT 'General'"),
            ("model", "VARCHAR(100) DEFAULT 'ConvGeM-NeXt'"),
            ("affected_area_ratio", "FLOAT DEFAULT 0.0"),
            ("affected_percent", "FLOAT DEFAULT 0.0"),
            ("is_leaf", "BOOLEAN DEFAULT TRUE"),
            ("leaf_confidence", "FLOAT DEFAULT 1.0"),
            ("classification_status", "VARCHAR(100) DEFAULT 'confirmed'")
        ]:
            try:
                conn.execute(text(f"SELECT {col} FROM disease_records LIMIT 1;"))
            except Exception:
                try:
                    conn.execute(text(f"ALTER TABLE disease_records ADD COLUMN {col} {col_type};"))
                    conn.commit()
                    print(f"Migrated: added {col} to disease_records table.")
                except Exception as em:
                    print(f"Migration disease_records.{col} failed: {em}")

    # Seed default demo farmer if table is empty
    from sqlalchemy.orm import Session
    from .utils.security import get_password_hash
    from .models import Farmer, Farm
    db = Session(bind=engine)
    try:
        demo_farmer = db.query(Farmer).filter(Farmer.phone_number == "0987654321").first()
        hashed = get_password_hash("password")
        if not demo_farmer:
            new_farmer = Farmer(
                full_name="Jhanandhan",
                phone_number="0987654321",
                password_hash=hashed,
                preferred_language="english",
                dark_mode=False
            )
            db.add(new_farmer)
            db.commit()
            db.refresh(new_farmer)
            
            # Default farm
            new_farm = Farm(
                farmer_id=new_farmer.id,
                farm_name="Primary Farm",
                location_district="Idukki",
                soil_type="Laterite",
                land_area_acres=1.5,
                water_availability="medium",
                irrigation_type="manual"
            )
            db.add(new_farm)
            db.commit()
            print("Seeded default demo farmer Jhanandhan (Idukki): 0987654321 / password successfully.")
        else:
            demo_farmer.full_name = "Jhanandhan"
            demo_farmer.password_hash = hashed
            farm = db.query(Farm).filter(Farm.farmer_id == demo_farmer.id).first()
            if farm:
                farm.location_district = "Idukki"
            db.commit()
            print("Updated demo farmer to Jhanandhan (Idukki) successfully.")
            print("Ensured demo farmer (0987654321) password hash matches 'password'.")
    except Exception as es:
        print(f"Demo seeding warning: {es}")
    finally:
        db.close()
except Exception as e:
    print(f"Database table check/creation warning: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Explainable Multi-Agent Personal Farming Assistant for Kerala Farmers",
    version="1.0.0",
)

# CORS configurations for React frontend
origins = [
    "http://localhost:5173", # Vite local server default
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for serving uploaded disease leaf images
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
os.makedirs(os.path.join(STATIC_DIR, "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(crop.router, prefix=settings.API_V1_STR)
app.include_router(disease.router, prefix=settings.API_V1_STR)
app.include_router(fertilizer.router, prefix=settings.API_V1_STR)
app.include_router(chatbot.router, prefix=settings.API_V1_STR)
app.include_router(market.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "project": "AgriGenie AI",
        "description": "Multi-Agent Agricultural Decision Platform for Kerala Farmers",
        "status": "Online",
        "api_docs": "/docs"
    }

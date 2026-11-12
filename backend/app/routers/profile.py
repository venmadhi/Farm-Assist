from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import datetime

from ..database import get_db
from ..models import Farmer, Farm, SoilTest, CropHistory, DiseaseRecord, WeatherHistory, CropPrediction, YieldPrediction, CropCycle, ModelVersion
from ..schemas import FarmerResponse, SoilTestCreate, SoilTestResponse, CropHistoryCreate, CropHistoryResponse, FarmCreate, FarmResponse, CropCycleCreate, CropCycleHarvest, CropCycleResponse, ModelVersionResponse
from .auth import get_current_farmer

router = APIRouter(prefix="/profile", tags=["Farmer Profile & Digital Twin"])

@router.get("/me", response_model=FarmerResponse)
def get_me(current_farmer: Farmer = Depends(get_current_farmer)):
    return current_farmer

@router.get("/twin")
def get_digital_twin_summary(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    # Ensure farmer has at least one farm
    primary_farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not primary_farm:
        primary_farm = Farm(
            farmer_id=current_farmer.id,
            farm_name="Primary Farm",
            location_district= "Palakkad",
            soil_type="Laterite",
            land_area_acres=1.0,
            water_availability="medium",
            irrigation_type="manual"
        )
        db.add(primary_farm)
        db.commit()
        db.refresh(primary_farm)

    # Retrieve all sub-tables associated with this farm
    soil_records = db.query(SoilTest).filter(SoilTest.farm_id == primary_farm.id).order_by(SoilTest.measured_at.asc()).all()
    history_records = db.query(CropHistory).filter(CropHistory.farm_id == primary_farm.id).order_by(CropHistory.year.desc()).all()
    disease_records = db.query(DiseaseRecord).filter(DiseaseRecord.farm_id == primary_farm.id).order_by(DiseaseRecord.scanned_at.desc()).all()
    weather_records = db.query(WeatherHistory).filter(WeatherHistory.farm_id == primary_farm.id).order_by(WeatherHistory.recorded_at.desc()).all()
    predictions = db.query(CropPrediction).filter(CropPrediction.farm_id == primary_farm.id).order_by(CropPrediction.predicted_at.desc()).all()

    # Fetch active and completed crop cycles
    active_cycles = db.query(CropCycle).filter(CropCycle.farm_id == primary_farm.id, CropCycle.status == "ACTIVE").order_by(CropCycle.start_date.desc()).all()
    completed_cycles = db.query(CropCycle).filter(CropCycle.farm_id == primary_farm.id, CropCycle.status == "HARVESTED").order_by(CropCycle.harvest_date.desc()).all()

    # --- AI DIGITAL TWIN METRICS CALCULATIONS ---
    
    # 1. Farm Health Score
    health_score = 90.0
    warnings = []
    
    if soil_records:
        latest_soil = soil_records[-1]
        # pH impact
        if latest_soil.ph < 5.5:
            health_score -= 15.0
            warnings.append(f"Highly acidic soil (pH {latest_soil.ph:.1f}) detected. Apply Dolomite/Lime to neutralize.")
        elif latest_soil.ph > 7.5:
            health_score -= 10.0
            warnings.append(f"Alkaline soil (pH {latest_soil.ph:.1f}) detected. Apply organic gypsum/manure.")
            
        # NPK deficiencies
        if latest_soil.nitrogen < 50:
            health_score -= 5.0
            warnings.append("Low Soil Nitrogen (N) levels. Consider nitrogen-fixing crops or organic compost.")
        if latest_soil.phosphorus < 30:
            health_score -= 5.0
            warnings.append("Low Soil Phosphorus (P) levels. Apply Rock Phosphate or Bone meal.")
        if latest_soil.potassium < 60:
            health_score -= 5.0
            warnings.append("Low Soil Potassium (K) levels. Apply Wood Ash or organic potash source.")
            
        # Organic Carbon
        if latest_soil.organic_carbon < 0.4:
            health_score -= 8.0
            warnings.append("Critical low Soil Organic Carbon. Add farmyard manure or vermicompost.")
    else:
        health_score = 75.0
        warnings.append("No recent soil testing record. Perform a soil test to update digital twin metrics.")

    # Disease impact
    recent_disease = [d for d in disease_records if (datetime.datetime.utcnow() - d.scanned_at).days < 30]
    if recent_disease:
        severity_deduction = 15.0 if any(d.severity_level.startswith("Severe") for d in recent_disease) else 8.0
        health_score -= severity_deduction
        warnings.append(f"Active leaf disease outbreaks detected ({recent_disease[0].detected_disease}). Implement recovery actions.")

    # Weather impact
    extreme_weather = False
    if weather_records:
        latest_weather = weather_records[0]
        if latest_weather.rainfall > 350.0 or latest_weather.temperature > 38.0:
            health_score -= 10.0
            extreme_weather = True
            warnings.append("Stress warning: Extreme local weather conditions detected.")

    health_score = max(15.0, min(100.0, health_score))

    # 2. Expected Yield & Profit Dynamic Mapping (No fabricated fallbacks)
    expected_yield_kg = 0.0
    expected_profit_inr = 0.0
    latest_crop = None
    
    if active_cycles:
        # Expected metrics are derived directly from the current active crop cycle
        primary_active = active_cycles[0]
        latest_crop = primary_active.crop_name
        expected_yield_kg = round(primary_active.expected_yield, 2)
        expected_profit_inr = round(primary_active.expected_profit, 2)
    elif completed_cycles:
        # Show most recently harvested crop
        latest_crop = completed_cycles[0].crop_name

    # 3. Overall Risk Score
    risk_score = 15.0 # baseline risk
    risk_reasons = []
    
    if health_score < 60:
        risk_score += 20.0
        risk_reasons.append("Poor soil organic/NPK profile")
    if recent_disease:
        risk_score += 25.0
        risk_reasons.append("Active crop leaf disease incidence")
    if extreme_weather:
        risk_score += 15.0
        risk_reasons.append("Extreme regional weather conditions")
    if not water_records_exist_or_low(primary_farm):
        risk_score += 10.0
        risk_reasons.append("Water stress / rain shortages")

    risk_score = max(5.0, min(95.0, risk_score))

    # Total metrics sum - derived from actual completed cycles
    total_yield = sum([c.actual_yield for c in completed_cycles if c.actual_yield])
    total_revenue = sum([c.actual_revenue for c in completed_cycles if c.actual_revenue])
    avg_ph = sum([s.ph for s in soil_records]) / len(soil_records) if soil_records else 6.2

    return {
        "farmer_profile": {
            "id": current_farmer.id,
            "full_name": current_farmer.full_name,
            "phone_number": current_farmer.phone_number,
            "location_district": primary_farm.location_district if primary_farm else "Idukki",
            "preferred_language": current_farmer.preferred_language,
            "dark_mode": current_farmer.dark_mode,
            "created_at": current_farmer.created_at,
            "farm": {
                "id": primary_farm.id,
                "farm_name": primary_farm.farm_name,
                "location_district": primary_farm.location_district,
                "soil_type": primary_farm.soil_type,
                "land_area_acres": primary_farm.land_area_acres,
                "water_availability": primary_farm.water_availability,
                "irrigation_type": primary_farm.irrigation_type,
                "latitude": primary_farm.latitude,
                "longitude": primary_farm.longitude
            }
        },
        "soil_health_score": round(health_score, 1),
        "soil_health_status": "Excellent" if health_score >= 85 else "Good" if health_score >= 70 else "Fair" if health_score >= 50 else "Critical Warning",
        "soil_warnings": warnings,
        "total_yield_kg": total_yield,
        "total_revenue_inr": total_revenue,
        "average_ph": round(avg_ph, 2),
        "digital_twin_metrics": {
            "health_score": round(health_score, 1),
            "expected_yield_kg": expected_yield_kg,
            "expected_profit_inr": expected_profit_inr,
            "risk_score": round(risk_score, 1),
            "risk_reasons": risk_reasons,
            "latest_crop": latest_crop
        },
        "soil_history": [
            {
                "id": s.id,
                "n": s.nitrogen,
                "p": s.phosphorus,
                "k": s.potassium,
                "ph": s.ph,
                "organic_carbon": s.organic_carbon,
                "measured_at": s.measured_at.strftime("%Y-%m-%d")
            } for s in soil_records
        ],
        "crop_history": [
            {
                "id": c.id,
                "crop": c.crop_name,
                "crop_name": c.crop_name,
                "yield": c.actual_yield,
                "season": c.season,
                "year": c.year,
                "revenue": c.actual_revenue,
                "fertilizer": c.fertilizer_used or "None",
                "disease": c.disease_incidence or "None",
                "expected_yield": c.expected_yield,
                "expected_profit": c.expected_profit,
                "actual_profit": c.actual_profit,
                "cultivation_cost": c.cultivation_cost,
                "actual_selling_price": c.actual_selling_price,
                "absolute_error": round(abs(c.expected_yield - c.actual_yield), 2) if (c.expected_yield is not None and c.actual_yield is not None) else None,
                "percentage_error": round((abs(c.expected_yield - c.actual_yield) / c.actual_yield * 100.0), 1) if (c.expected_yield is not None and c.actual_yield and c.actual_yield > 0) else 0.0,
                "harvest_date": c.harvest_date.strftime("%Y-%m-%d") if c.harvest_date else None,
                "start_date": c.start_date.strftime("%Y-%m-%d") if c.start_date else None
            } for c in completed_cycles
        ],
        "active_cycles": [
            {
                "id": c.id,
                "crop": c.crop_name,
                "crop_name": c.crop_name,
                "season": c.season,
                "year": c.year,
                "area_acres": c.area_acres,
                "expected_yield": c.expected_yield,
                "expected_profit": c.expected_profit,
                "expected_revenue": c.expected_revenue,
                "start_date": c.start_date.strftime("%Y-%m-%d") if c.start_date else None
            } for c in active_cycles
        ],
        "recent_recommendations": [
            {
                "id": r.id,
                "crop": r.recommended_crop,
                "confidence": r.confidence_score,
                "yield": r.expected_yield,
                "profit": r.estimated_profit,
                "date": r.predicted_at.strftime("%Y-%m-%d")
            } for r in predictions[:5]
        ]
    }

def water_records_exist_or_low(farm: Farm) -> bool:
    if farm.water_availability == "low":
        return False
    return True

@router.post("/soil", response_model=SoilTestResponse)
def add_soil_record(
    soil_in: SoilTestCreate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    primary_farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not primary_farm:
        raise HTTPException(status_code=404, detail="Farm profile not found. Register a farm first.")

    new_soil = SoilTest(
        farm_id=primary_farm.id,
        nitrogen=soil_in.nitrogen,
        phosphorus=soil_in.phosphorus,
        potassium=soil_in.potassium,
        ph=soil_in.ph,
        organic_carbon=soil_in.organic_carbon,
        boron=soil_in.boron,
        iron=soil_in.iron,
        zinc=soil_in.zinc
    )
    db.add(new_soil)
    db.commit()
    db.refresh(new_soil)
    return new_soil

@router.post("/crop-history", response_model=CropHistoryResponse)
def add_crop_history(
    history_in: CropHistoryCreate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    primary_farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not primary_farm:
        raise HTTPException(status_code=404, detail="Farm profile not found.")

    new_history = CropHistory(
        farm_id=primary_farm.id,
        crop_name=history_in.crop_name,
        yield_kg=history_in.yield_kg,
        revenue=history_in.revenue,
        season=history_in.season,
        year=history_in.year,
        weather_summary=history_in.weather_summary,
        disease_incidence=history_in.disease_incidence,
        fertilizer_used=history_in.fertilizer_used,
        market_price=history_in.market_price,
        harvest_date=datetime.datetime.combine(history_in.end_date, datetime.time.min),
        start_date=datetime.datetime.combine(history_in.start_date, datetime.time.min)
    )
    db.add(new_history)
    
    from sqlalchemy import func
    existing_cycle = db.query(CropCycle).filter(
        CropCycle.farm_id == primary_farm.id,
        func.lower(CropCycle.crop_name) == func.lower(history_in.crop_name.strip()),
        CropCycle.season == history_in.season,
        CropCycle.year == history_in.year
    ).first()
    
    start_dt = datetime.datetime.combine(history_in.start_date, datetime.time.min) if hasattr(history_in, 'start_date') and history_in.start_date else datetime.datetime.utcnow()
    end_dt = datetime.datetime.combine(history_in.end_date, datetime.time.min) if hasattr(history_in, 'end_date') and history_in.end_date else datetime.datetime.utcnow()
    
    if existing_cycle:
        existing_cycle.actual_yield = history_in.yield_kg
        existing_cycle.actual_revenue = history_in.revenue
        existing_cycle.actual_profit = (history_in.revenue or 0.0) - (existing_cycle.cultivation_cost or 0.0)
        existing_cycle.actual_selling_price = history_in.market_price
        existing_cycle.fertilizer_used = history_in.fertilizer_used
        existing_cycle.disease_incidence = history_in.disease_incidence
        existing_cycle.start_date = start_dt
        existing_cycle.harvest_date = end_dt
        existing_cycle.status = "HARVESTED"
    else:
        # Save a matching completed CropCycle record
        new_cycle = CropCycle(
            farm_id=primary_farm.id,
            crop_name=history_in.crop_name,
            season=history_in.season,
            year=history_in.year,
            area_acres=primary_farm.land_area_acres,
            expected_yield=history_in.yield_kg,
            actual_yield=history_in.yield_kg,
            expected_revenue=history_in.revenue or 0.0,
            actual_revenue=history_in.revenue,
            expected_profit=0.0,
            actual_profit=history_in.revenue or 0.0,
            actual_selling_price=history_in.market_price,
            cultivation_cost=0.0,
            fertilizer_used=history_in.fertilizer_used,
            disease_incidence=history_in.disease_incidence,
            status="HARVESTED",
            start_date=start_dt,
            harvest_date=end_dt
        )
        db.add(new_cycle)
    
    db.commit()
    db.refresh(new_history)
    return new_history

@router.post("/farm-update", response_model=FarmResponse)
def update_farm_profile(
    farm_in: FarmCreate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    primary_farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not primary_farm:
        primary_farm = Farm(farmer_id=current_farmer.id)
        db.add(primary_farm)
        
    primary_farm.farm_name = farm_in.farm_name
    primary_farm.location_district = farm_in.location_district
    primary_farm.latitude = farm_in.latitude
    primary_farm.longitude = farm_in.longitude
    primary_farm.soil_type = farm_in.soil_type
    primary_farm.land_area_acres = farm_in.land_area_acres
    primary_farm.water_availability = farm_in.water_availability
    primary_farm.irrigation_type = farm_in.irrigation_type
    
    db.commit()
    db.refresh(primary_farm)
    return primary_farm

@router.get("/weather")
def get_live_weather(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    primary_farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not primary_farm:
        raise HTTPException(status_code=404, detail="Farm not found.")

    # Use coordinates if supplied, else fallback to primary farm coords
    latitude = lat if lat is not None else (primary_farm.latitude or 10.7867)
    longitude = lon if lon is not None else (primary_farm.longitude or 76.6548)
    district = primary_farm.location_district or "Palakkad"

    # Dynamic season calculator based on month
    current_month = datetime.datetime.now().month
    # Kerala seasons mapping
    if current_month in [6, 7, 8, 9]:
        season = "Southwest Monsoon (Kharif)"
    elif current_month in [10, 11, 12, 1]:
        season = "Northeast Monsoon (Rabi)"
    else:
        season = "Summer (Zaid)"

    # Attempt to fetch live weather from Open-Meteo
    temp = 28.5
    humidity = 72.0
    rain = 0.0
    wind_speed = 12.0
    pressure = 1012.0
    uv_index = 5.0
    alert = "Normal Weather Conditions"

    try:
        import requests
        api_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,rain,surface_pressure,wind_speed_10m"
        resp = requests.get(api_url, timeout=5)
        if resp.status_code == 200:
            weather_data = resp.json().get("current", {})
            temp = weather_data.get("temperature_2m", temp)
            humidity = weather_data.get("relative_humidity_2m", humidity)
            rain = weather_data.get("rain", rain)
            wind_speed = weather_data.get("wind_speed_10m", wind_speed)
            pressure = weather_data.get("surface_pressure", pressure)
            
            # Simple alert thresholds
            if rain > 50.0:
                alert = "Heavy rain alert! Clear drainage channels."
            elif temp > 36.0:
                alert = "Heat warning. Keep plants irrigated."
    except Exception as e:
        print(f"Failed to fetch live weather: {e}. Falling back to district simulator.")
        # Local district-month weather simulation fallbacks
        if "idukki" in district.lower() or "munnar" in district.lower():
            temp = 18.5 if current_month in [11, 12, 1] else 22.0
            humidity = 85.0
            rain = 15.0 if season.startswith("Southwest") else 2.0
        elif "palakkad" in district.lower():
            temp = 34.0 if current_month in [3, 4, 5] else 28.0
            humidity = 60.0
            rain = 8.0 if season.startswith("Southwest") else 0.0

    # Save to WeatherHistory database table
    new_weather = WeatherHistory(
        farm_id=primary_farm.id,
        temperature=temp,
        humidity=humidity,
        rainfall=rain,
        wind_speed=wind_speed,
        pressure=pressure,
        uv_index=uv_index,
        weather_alerts=alert
    )
    db.add(new_weather)
    db.commit()

    return {
        "district": district,
        "latitude": latitude,
        "longitude": longitude,
        "temperature": round(temp, 1),
        "humidity": round(humidity, 1),
        "rainfall": round(rain, 2),
        "wind_speed": round(wind_speed, 1),
        "pressure": round(pressure, 1),
        "uv_index": uv_index,
        "weather_alerts": alert,
        "season": season
    }


@router.post("/crop-cycle", response_model=CropCycleResponse)
def start_crop_cycle(
    cycle_in: CropCycleCreate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    primary_farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not primary_farm:
        raise HTTPException(status_code=404, detail="Primary farm not found.")
        
    # Check if there is already an active cycle for this crop
    existing = db.query(CropCycle).filter(
        CropCycle.farm_id == primary_farm.id,
        CropCycle.crop_name == cycle_in.crop_name,
        CropCycle.status == "ACTIVE"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"An active crop cycle for {cycle_in.crop_name} already exists.")

    start_date_val = datetime.datetime.combine(cycle_in.start_date, datetime.datetime.min.time()) if cycle_in.start_date else datetime.datetime.utcnow()

    new_cycle = CropCycle(
        farm_id=primary_farm.id,
        crop_name=cycle_in.crop_name,
        season=cycle_in.season,
        year=cycle_in.year,
        area_acres=cycle_in.area_acres,
        expected_yield=cycle_in.expected_yield,
        expected_profit=cycle_in.expected_profit,
        expected_revenue=cycle_in.expected_revenue,
        status="ACTIVE",
        start_date=start_date_val
    )
    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)
    return new_cycle


RETRAINING_ERROR_THRESHOLD = 50.0  # Configurable prediction percentage error threshold (%)

@router.post("/crop-cycle/{cycle_id}/harvest", response_model=CropCycleResponse)
def harvest_crop_cycle(
    cycle_id: int,
    harvest_in: CropCycleHarvest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    cycle = db.query(CropCycle).filter(CropCycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Crop cycle not found.")
        
    if harvest_in.actual_yield <= 0:
        raise HTTPException(status_code=400, detail="Actual yield must be greater than 0 kg.")
    if harvest_in.actual_selling_price < 0:
        raise HTTPException(status_code=400, detail="Actual selling price cannot be negative.")
    if harvest_in.cultivation_cost < 0:
        raise HTTPException(status_code=400, detail="Actual cultivation cost cannot be negative.")
        
    # Calculate actual revenue and profit from farmer inputs ONLY
    actual_revenue = round(harvest_in.actual_yield * harvest_in.actual_selling_price, 2)
    actual_profit = round(actual_revenue - harvest_in.cultivation_cost, 2)
    
    # Handle dates accurately
    if harvest_in.start_date:
        cycle.start_date = datetime.datetime.combine(harvest_in.start_date, datetime.datetime.min.time())
    
    if harvest_in.harvest_date:
        harvest_date_val = datetime.datetime.combine(harvest_in.harvest_date, datetime.datetime.min.time())
    else:
        harvest_date_val = datetime.datetime.utcnow()
        
    if cycle.start_date and harvest_date_val < cycle.start_date:
        raise HTTPException(status_code=400, detail="Harvest date cannot be earlier than cultivation start date.")
    
    cycle.actual_yield = harvest_in.actual_yield
    cycle.actual_selling_price = harvest_in.actual_selling_price
    cycle.cultivation_cost = harvest_in.cultivation_cost
    cycle.actual_revenue = actual_revenue
    cycle.actual_profit = actual_profit
    cycle.fertilizer_used = harvest_in.fertilizer_used or "None"
    cycle.disease_incidence = harvest_in.disease_incidence or "None"
    cycle.status = "HARVESTED"
    cycle.harvest_date = harvest_date_val
    
    # Save a record to the CropHistory table with exact farmer harvest details
    new_history = CropHistory(
        farm_id=cycle.farm_id,
        crop_name=cycle.crop_name,
        yield_kg=harvest_in.actual_yield,
        revenue=actual_revenue,
        season=cycle.season,
        year=cycle.year,
        weather_summary="Normal",
        disease_incidence=harvest_in.disease_incidence or "None",
        fertilizer_used=harvest_in.fertilizer_used or "None",
        market_price=harvest_in.actual_selling_price,
        harvest_date=harvest_date_val,
        start_date=cycle.start_date
    )
    db.add(new_history)
    db.commit()
    db.refresh(cycle)
    
    # Evaluate prediction error against retraining threshold
    expected_yield = cycle.expected_yield or 0.0
    actual_yield = harvest_in.actual_yield
    abs_error = abs(expected_yield - actual_yield)
    percentage_error = (abs_error / actual_yield * 100.0) if actual_yield > 0 else 0.0
    
    if percentage_error > RETRAINING_ERROR_THRESHOLD:
        print(f"[Harvest Feedback] Retraining evaluation: Prediction error is {percentage_error:.1f}% (Threshold: {RETRAINING_ERROR_THRESHOLD}%). Marked as candidate for model improvement.")
    else:
        print(f"[Harvest Feedback] Retraining evaluation: Prediction error is {percentage_error:.1f}% <= {RETRAINING_ERROR_THRESHOLD}%. Prediction is acceptable, no retraining triggered.")
        
    return cycle


@router.get("/crop-cycles", response_model=List[CropCycleResponse])
def get_crop_cycles(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    primary_farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not primary_farm:
        return []
    return db.query(CropCycle).filter(CropCycle.farm_id == primary_farm.id).order_by(CropCycle.created_at.desc()).all()


@router.post("/model-retrain")
def manual_model_retrain(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    # Check completed cycles for meaningful prediction errors above threshold
    primary_farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not primary_farm:
        return {"triggered": False, "message": "No farm profile found."}
        
    completed_cycles = db.query(CropCycle).filter(CropCycle.farm_id == primary_farm.id, CropCycle.status == "HARVESTED").all()
    candidates = [
        c for c in completed_cycles 
        if c.actual_yield and c.actual_yield > 0 and (abs(c.expected_yield - c.actual_yield) / c.actual_yield * 100.0) > RETRAINING_ERROR_THRESHOLD
    ]
    
    if not candidates:
        return {
            "triggered": False, 
            "message": f"All {len(completed_cycles)} historical crop prediction(s) are within acceptable error tolerance (<= {RETRAINING_ERROR_THRESHOLD}% error). Retraining is not required."
        }
    
    return {
        "triggered": False, 
        "message": f"Identified {len(candidates)} candidate record(s) exceeding {RETRAINING_ERROR_THRESHOLD}% error threshold. Feedback records preserved for ML model improvement."
    }



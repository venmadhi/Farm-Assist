from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Farm, FertilizerHistory, WeatherHistory
from ..schemas import FertilizerRequest, FertilizerResponse
from .auth import get_current_farmer
from ..ml.fertilizer_agent import fertilizer_agent

router = APIRouter(prefix="/fertilizer", tags=["Smart Fertilizer Agent"])

@router.post("/calculate", response_model=FertilizerResponse)
def calculate_crop_fertilizer_schedule(
    request: FertilizerRequest,
    current_farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    # Get current farmer's primary farm
    farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not farm:
        farm = Farm(
            farmer_id=current_farmer.id,
            farm_name="Primary Farm",
            location_district="Palakkad",
            latitude=10.7867,
            longitude=76.6548,
            soil_type="Laterite",
            land_area_acres=1.0,
            water_availability="medium",
            irrigation_type="manual"
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

    weather = db.query(WeatherHistory).filter(WeatherHistory.farm_id == farm.id).order_by(WeatherHistory.recorded_at.desc()).first()
    if not weather:
        raise HTTPException(
            status_code=400,
            detail="Recent temperature and humidity data are required but missing from the database. Please record weather data first."
        )

    try:
        result = fertilizer_agent.calculate_fertilizer(
            crop=request.crop_name,
            n=request.nitrogen,
            p=request.phosphorus,
            k=request.potassium,
            ph=request.ph,
            soil_type=farm.soil_type or "Laterite",
            temperature=weather.temperature,
            humidity=weather.humidity
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Save the calculation event to FertilizerHistory
    first_sch = result["fertilizer_schedule"][1] if len(result["fertilizer_schedule"]) > 1 else result["fertilizer_schedule"][0]
    
    new_history = FertilizerHistory(
        farm_id=farm.id,
        crop_name=request.crop_name,
        fertilizer_name=first_sch["fertilizer_name"],
        dosage_grams_per_sqm=first_sch["amount_grams_per_sqm"],
        organic_alternative_used=False,
        cost=result.get("estimated_cost", 0.0)
    )
    db.add(new_history)
    db.commit()

    return FertilizerResponse(
        crop_name=result["crop_name"],
        n_status=result["n_status"],
        p_status=result["p_status"],
        k_status=result["k_status"],
        fertilizer_schedule=result["fertilizer_schedule"],
        sustainability_tips=result["sustainability_tips"],
        estimated_cost=result["estimated_cost"]
    )

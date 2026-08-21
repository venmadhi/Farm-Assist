import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Farmer, Farm, SoilTest, CropPrediction, RecommendationHistory
from ..schemas import CropPredictRequest, CropPredictResponse, SHAPExplanation, RecommendedCropItem, FeedbackCreate, FeedbackResponse
from .auth import get_current_farmer
from ..ml.crop_agent import crop_agent

router = APIRouter(prefix="/crop", tags=["Crop Intelligence Agent"])

@router.post("/recommend", response_model=CropPredictResponse)
def get_crop_recommendation(
    request: CropPredictRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
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

    # Save soil test record automatically
    new_soil = SoilTest(
        farm_id=farm.id,
        nitrogen=request.nitrogen,
        phosphorus=request.phosphorus,
        potassium=request.potassium,
        ph=request.ph,
        organic_carbon=request.organic_carbon or 0.5,
        boron=request.boron or 0.2,
        iron=request.iron or 4.5,
        zinc=request.zinc or 0.6
    )
    db.add(new_soil)
    db.commit()

    # Run the machine learning model inference and SHAP explainability
    recommendation_data_list = crop_agent.recommend(
        db=db,
        farm_id=farm.id,
        n=request.nitrogen,
        p=request.phosphorus,
        k=request.potassium,
        ph=request.ph,
        organic_carbon=request.organic_carbon or 0.5,
        boron=request.boron or 0.2,
        iron=request.iron or 4.5,
        zinc=request.zinc or 0.6,
        temp=request.temperature,
        humidity=request.humidity,
        rainfall=request.rainfall,
        season=request.season or "Kharif"
    )

    response_items = []
    
    # Save the top predictions to CropPrediction table
    for idx, rec in enumerate(recommendation_data_list):
        new_prediction = CropPrediction(
            farm_id=farm.id,
            recommended_crop=rec["crop_name"],
            confidence_score=rec["confidence_score"],
            expected_yield=rec["expected_yield"],
            estimated_profit=rec["estimated_profit"],
            water_requirement=rec["water_requirement"],
            growing_duration_days=rec["growing_duration_days"],
            disease_risk=rec["disease_risk"],
            market_demand=rec["market_demand"],
            reason=rec["reason"],
            shap_explanation=json.dumps(rec["shap_contributions"])
        )
        db.add(new_prediction)
        db.commit()
        db.refresh(new_prediction)
        
        # We store prediction ID for the front-end to log feedback on the top recommendation
        rec_id = new_prediction.id if idx == 0 else 0
        
        response_items.append(
            RecommendedCropItem(
                crop_name=rec["crop_name"],
                confidence_score=rec["confidence_score"],
                expected_yield=rec["expected_yield"],
                estimated_profit=rec["estimated_profit"],
                water_requirement=rec["water_requirement"],
                growing_duration_days=rec["growing_duration_days"],
                disease_risk=rec["disease_risk"],
                market_demand=rec["market_demand"],
                reason=rec["reason"],
                shap_contributions=SHAPExplanation(
                    nitrogen=rec["shap_contributions"]["nitrogen"],
                    phosphorus=rec["shap_contributions"]["phosphorus"],
                    potassium=rec["shap_contributions"]["potassium"],
                    weather=rec["shap_contributions"]["weather"]
                )
            )
        )
        
    return CropPredictResponse(predictions=response_items)

@router.post("/feedback", response_model=FeedbackResponse)
def submit_recommendation_feedback(
    feedback_in: FeedbackCreate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    # Verify the prediction exists
    pred = db.query(CropPrediction).filter(CropPrediction.id == feedback_in.crop_prediction_id).first()
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop prediction record not found."
        )
        
    # Check if feedback already submitted
    existing_feedback = db.query(RecommendationHistory).filter(RecommendationHistory.crop_prediction_id == pred.id).first()
    if existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback already logged for this prediction."
        )
        
    new_feedback = RecommendationHistory(
        crop_prediction_id=pred.id,
        rating_1_to_5=feedback_in.rating_1_to_5,
        farmer_comment=feedback_in.comment,
        actual_outcome=feedback_in.actual_outcome or "pending"
    )
    db.add(new_feedback)
    
    # Adaptive learning log
    if feedback_in.rating_1_to_5 <= 2:
        print(f"Poor suitability feedback recorded for {pred.recommended_crop}. Digital Twin weights will penalize.")
        
    db.commit()
    db.refresh(new_feedback)
    
    return FeedbackResponse(
        id=new_feedback.id,
        crop_prediction_id=new_feedback.crop_prediction_id,
        rating_1_to_5=new_feedback.rating_1_to_5,
        comment=new_feedback.farmer_comment,
        actual_outcome=new_feedback.actual_outcome,
        submitted_at=new_feedback.submitted_at
    )

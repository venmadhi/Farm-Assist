import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Farmer, Farm, DiseaseRecord
from ..schemas import DiseaseRecordResponse
from .auth import get_current_farmer
from ..ml.disease_agent import disease_agent

router = APIRouter(prefix="/disease", tags=["Disease Detection Agent"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "uploads"))

@router.post("/scan", response_model=DiseaseRecordResponse)
def scan_leaf_image(
    file: UploadFile = File(...),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    # Verify file is an image
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File uploaded is not an image."
        )

    # Get or create farmer's primary farm
    farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not farm:
        farm = Farm(
            farmer_id=current_farmer.id,
            name=f"{current_farmer.full_name}'s Farm",
            location=current_farmer.location or "Idukki, Kerala",
            crop_type="Cardamom",
            soil_type="Loamy",
            farm_size_acres=2.5
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save the file with a unique name to prevent collisions
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded image: {e}"
        )

    # Perform CV model inference and severity scoring
    try:
        result = disease_agent.analyze_image(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing image: {e}"
        )

    # Save to Database under Farmer's Digital Twin (relative path)
    relative_path = f"/static/uploads/{unique_filename}"
    
    new_record = DiseaseRecord(
        farm_id=farm.id,
        image_path=relative_path,
        detected_disease=result["detected_disease"],
        confidence=result["confidence"],
        severity_level=result["severity_level"],
        treatment_plan=result["treatment_plan"],
        recovery_time_days=result.get("recovery_time_days", 14),
        crop=result.get("crop", "General"),
        model=result.get("model", "ConvGeM-NeXt"),
        affected_area_ratio=result.get("affected_area_ratio", 0.0),
        affected_percent=result.get("affected_percent", 0.0),
        is_leaf=result.get("is_leaf", True),
        leaf_confidence=result.get("leaf_confidence", 1.0),
        classification_status=result.get("classification_status", "confirmed")
    )
    
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    return new_record

@router.get("/history", response_model=List[DiseaseRecordResponse])
def get_disease_scan_history(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    farm = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).first()
    if not farm:
        return []
        
    records = db.query(DiseaseRecord).filter(
        DiseaseRecord.farm_id == farm.id
    ).order_by(DiseaseRecord.scanned_at.desc()).all()
    return records

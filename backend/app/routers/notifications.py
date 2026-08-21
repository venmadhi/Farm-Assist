from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Farmer, Notification
from ..schemas import NotificationResponse
from .auth import get_current_farmer

router = APIRouter(prefix="/notifications", tags=["Notification Services"])

@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    alerts = db.query(Notification).filter(
        Notification.farmer_id == current_farmer.id
    ).order_by(Notification.created_at.desc()).all()
    return alerts

@router.post("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    alert = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.farmer_id == current_farmer.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Notification not found.")
        
    alert.is_read = True
    db.commit()
    return {"message": "Notification marked as read successfully."}

@router.post("/trigger-demo")
def trigger_demo_notifications(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    # Check if demo alerts already exist to avoid redundancy
    existing = db.query(Notification).filter(Notification.farmer_id == current_farmer.id).first()
    if existing:
        return {"message": "Demo alerts already seeded."}

    alerts = [
        Notification(
            farmer_id=current_farmer.id,
            title="Heavy Rainfall Warning 🌧️",
            message="Yellow Alert triggered for Idukki/Palakkad district: Expected rainfall over 120mm in 24 hours. Ensure drainage trenches are clear.",
            category="weather"
        ),
        Notification(
            farmer_id=current_farmer.id,
            title="Sigatoka Spore Outbreak Alert 🦠",
            message="Disease outbreaks reported in adjacent banana groves in Wayanad. Prophylactically apply bio-agent Pseudomonas fluorescens.",
            category="disease"
        ),
        Notification(
            farmer_id=current_farmer.id,
            title="Market Price Increase 📈",
            message="Nendran Banana prices rose to ₹48.5/kg at Nedumangad market. Optimal harvesting time forecasted for next 10 days.",
            category="market"
        ),
        Notification(
            farmer_id=current_farmer.id,
            title="Model Retraining Completed 🧞‍♂️",
            message="All AgriGenie ML suite classifiers and regressors retrained on new historical harvest metrics.",
            category="system"
        )
    ]
    
    db.add_all(alerts)
    db.commit()
    return {"message": "Demo notifications triggered and saved successfully."}

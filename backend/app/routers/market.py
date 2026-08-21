from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import MarketPrices
from ..schemas import MarketPriceResponse
from .auth import get_current_farmer
from ..ml.market_agent import market_agent

router = APIRouter(prefix="/market", tags=["Market Intelligence Agent"])

@router.get("/trends", response_model=MarketPriceResponse)
def get_crop_market_trends(
    crop: str = Query(..., description="Crop name to query trends for"),
    district: Optional[str] = Query("Palakkad", description="Kerala district for localized pricing"),
    current_farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    try:
        result = market_agent.get_market_forecast(crop=crop, district=district)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Save/update price indicators in the database
    db_price = db.query(MarketPrices).filter(
        MarketPrices.crop_name == crop, 
        MarketPrices.district == district
    ).first()
    
    if not db_price:
        db_price = MarketPrices(
            crop_name=crop,
            district=district,
            price_today=result["current_market_price"],
            price_forecast_7d=result["price_forecast_7d"],
            price_forecast_30d=result["price_forecast_30d"],
            best_selling_month=result["best_selling_month"],
            demand_trend=result["price_trend"]
        )
        db.add(db_price)
    else:
        db_price.price_today = result["current_market_price"]
        db_price.price_forecast_7d = result["price_forecast_7d"]
        db_price.price_forecast_30d = result["price_forecast_30d"]
        db_price.best_selling_month = result["best_selling_month"]
        db_price.demand_trend = result["price_trend"]
        
    db.commit()
    
    return MarketPriceResponse(
        crop_name=result["crop"],
        district=district,
        price_today=result["current_market_price"],
        price_forecast_7d=result["price_forecast_7d"],
        price_forecast_30d=result["price_forecast_30d"],
        best_selling_month=result["best_selling_month"],
        demand_trend=result["price_trend"],
        historical_prices=result["historical_prices"],
        projected_profit=result.get("projected_profit", 0.0),
        investment_cost=result.get("investment_cost", 0.0),
        harvest_cycle_months=result.get("harvest_cycle_months", 0)
    )

from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

# --- AUTH SCHEMAS ---

class FarmerRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=50)
    phone_number: str = Field(..., pattern=r"^\+?[0-9]{10,12}$")
    password: str = Field(..., min_length=6)
    location_district: Optional[str] = "Palakkad"
    soil_type: Optional[str] = "Laterite"
    land_area_acres: Optional[float] = 1.0
    preferred_language: Optional[str] = "english"

class FarmerLogin(BaseModel):
    phone_number: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone_number: Optional[str] = None
    farmer_id: Optional[int] = None

# --- FARM SCHEMAS ---

class FarmCreate(BaseModel):
    farm_name: str
    location_district: str
    latitude: Optional[float] = 10.7867
    longitude: Optional[float] = 76.6548
    soil_type: str
    land_area_acres: float
    water_availability: str
    irrigation_type: str

class FarmResponse(BaseModel):
    id: int
    farmer_id: int
    farm_name: str
    location_district: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    soil_type: Optional[str]
    land_area_acres: float
    water_availability: str
    irrigation_type: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- SOIL TEST SCHEMAS ---

class SoilTestCreate(BaseModel):
    nitrogen: float = Field(..., ge=0, le=300)
    phosphorus: float = Field(..., ge=0, le=300)
    potassium: float = Field(..., ge=0, le=300)
    ph: float = Field(..., ge=0, le=14)
    organic_carbon: Optional[float] = 0.5
    boron: Optional[float] = 0.2
    iron: Optional[float] = 4.5
    zinc: Optional[float] = 0.6

class SoilTestResponse(BaseModel):
    id: int
    farm_id: int
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    organic_carbon: float
    boron: float
    iron: float
    zinc: float
    measured_at: datetime.datetime

    class Config:
        from_attributes = True

# --- CROP HISTORY SCHEMAS ---

class CropHistoryCreate(BaseModel):
    crop_name: str
    yield_kg: float
    revenue: Optional[float] = None
    season: str
    year: int
    weather_summary: Optional[str] = None
    disease_incidence: Optional[str] = None
    fertilizer_used: Optional[str] = None
    market_price: Optional[float] = None

class CropHistoryResponse(BaseModel):
    id: int
    farm_id: int
    crop_name: str
    yield_kg: float
    revenue: Optional[float]
    season: str
    year: int
    weather_summary: Optional[str]
    disease_incidence: Optional[str]
    fertilizer_used: Optional[str]
    market_price: Optional[float]
    harvest_date: datetime.datetime

    class Config:
        from_attributes = True

# --- WEATHER SCHEMAS ---

class WeatherHistoryCreate(BaseModel):
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: Optional[float] = 0.0
    pressure: Optional[float] = 1013.0
    uv_index: Optional[float] = 1.0
    weather_alerts: Optional[str] = None

class WeatherHistoryResponse(BaseModel):
    id: int
    farm_id: int
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    pressure: float
    uv_index: float
    weather_alerts: Optional[str]
    recorded_at: datetime.datetime

    class Config:
        from_attributes = True

# --- FARMER RESPONSE SCHEMA ---

class FarmerResponse(BaseModel):
    id: int
    full_name: str
    phone_number: str
    preferred_language: str
    dark_mode: bool
    created_at: datetime.datetime
    farms: List[FarmResponse] = []

    class Config:
        from_attributes = True

# --- RECOMMENDATION & ML SCHEMAS ---

class CropPredictRequest(BaseModel):
    farm_id: int
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    organic_carbon: Optional[float] = 0.5
    boron: Optional[float] = 0.2
    iron: Optional[float] = 4.5
    zinc: Optional[float] = 0.6
    temperature: Optional[float] = 28.0
    humidity: Optional[float] = 75.0
    rainfall: Optional[float] = 1500.0
    season: Optional[str] = "Kharif"

class SHAPExplanation(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float
    weather: float

class RecommendedCropItem(BaseModel):
    crop_name: str
    confidence_score: float # Final Recommendation Score
    expected_yield: float
    estimated_profit: float
    water_requirement: float
    growing_duration_days: int
    disease_risk: str
    market_demand: str
    reason: str
    shap_contributions: SHAPExplanation
    soil_score: Optional[float] = None
    climate_score: Optional[float] = None
    rotation_score: Optional[float] = None
    profit_score: Optional[float] = None
    rank: Optional[int] = None

class CropPredictResponse(BaseModel):
    predictions: List[RecommendedCropItem]
    cycle: Optional[int] = 1
    previousCrop: Optional[str] = None
    previousCropStatus: Optional[str] = None
    rotationApplied: Optional[bool] = False
    selectedRecommendation: Optional[str] = None

class FertilizerRequest(BaseModel):
    farm_id: int
    crop_name: str
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float

class FertilizerScheduleItem(BaseModel):
    stage: str
    fertilizer_name: str
    amount_grams_per_sqm: float
    organic_alternatives: List[str]

class FertilizerResponse(BaseModel):
    crop_name: str
    n_status: str
    p_status: str
    k_status: str
    fertilizer_schedule: List[FertilizerScheduleItem]
    sustainability_tips: List[str]
    estimated_cost: float

# --- YIELD PREDICTION SCHEMA ---

class YieldPredictRequest(BaseModel):
    farm_id: int
    crop_name: str
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    rainfall: float
    temperature: float

class YieldPredictResponse(BaseModel):
    crop_name: str
    predicted_yield_kg: float
    confidence: float
    expected_harvest_date: datetime.date
    profit_estimate: float

# --- MARKET SCHEMAS ---

class MarketPriceResponse(BaseModel):
    crop_name: str
    district: str
    price_today: float
    price_forecast_7d: Optional[float]
    price_forecast_30d: float
    best_selling_month: str
    demand_trend: str
    historical_prices: List[dict] = []
    projected_profit: Optional[float] = 0.0
    investment_cost: Optional[float] = 0.0
    harvest_cycle_months: Optional[int] = 0

# --- DISEASE SCHEMAS ---

class DiseaseRecordResponse(BaseModel):
    id: int
    farm_id: int
    detected_disease: str
    confidence: float
    severity_level: str
    treatment_plan: str
    image_path: str
    recovery_time_days: int
    crop: Optional[str] = "General"
    model: Optional[str] = "ConvGeM-NeXt"
    affected_area_ratio: Optional[float] = 0.0
    affected_percent: Optional[float] = 0.0
    is_leaf: Optional[bool] = True
    leaf_confidence: Optional[float] = 1.0
    classification_status: Optional[str] = "confirmed"
    scanned_at: datetime.datetime

    class Config:
        from_attributes = True

# --- NOTIFICATION SCHEMAS ---

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    category: str
    is_read: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- FEEDBACK SCHEMAS ---

class FeedbackCreate(BaseModel):
    crop_prediction_id: int
    rating_1_to_5: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    actual_outcome: Optional[str] = "pending"

class FeedbackResponse(BaseModel):
    id: int
    crop_prediction_id: int
    rating_1_to_5: int
    farmer_comment: Optional[str]
    actual_outcome: Optional[str]
    submitted_at: datetime.datetime

    class Config:
        from_attributes = True


# --- CROP CYCLE SCHEMAS ---

class CropCycleCreate(BaseModel):
    crop_name: str
    season: str
    year: int
    area_acres: float
    expected_yield: float
    expected_profit: float
    expected_revenue: float

class CropCycleHarvest(BaseModel):
    actual_yield: float
    actual_selling_price: float
    cultivation_cost: float
    fertilizer_used: Optional[str] = None
    disease_incidence: Optional[str] = None

class CropCycleResponse(BaseModel):
    id: int
    farm_id: int
    crop_name: str
    season: str
    year: int
    start_date: datetime.datetime
    harvest_date: Optional[datetime.datetime] = None
    area_acres: float
    expected_yield: float
    actual_yield: Optional[float] = None
    expected_revenue: float
    actual_revenue: Optional[float] = None
    expected_profit: float
    actual_profit: Optional[float] = None
    actual_selling_price: Optional[float] = None
    cultivation_cost: Optional[float] = None
    fertilizer_used: Optional[str] = None
    disease_incidence: Optional[str] = None
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- MODEL VERSION SCHEMAS ---

class ModelVersionResponse(BaseModel):
    id: int
    model_name: str
    version: str
    training_date: datetime.datetime
    dataset_version: str
    training_records_count: int
    validation_metric_name: str
    validation_metric_value: float
    test_metric_value: Optional[float] = None
    is_active: bool

    class Config:
        from_attributes = True


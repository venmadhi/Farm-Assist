import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    preferred_language = Column(String(50), default="english")
    dark_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="farmer", cascade="all, delete-orphan")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    farm_name = Column(String(255), nullable=False, default="Primary Farm")
    location_district = Column(String(100), nullable=True, default="Palakkad")
    latitude = Column(Float, nullable=True, default=10.7867)
    longitude = Column(Float, nullable=True, default=76.6548)
    soil_type = Column(String(100), nullable=True, default="Laterite")
    land_area_acres = Column(Float, default=1.0)
    water_availability = Column(String(50), default="medium")
    irrigation_type = Column(String(50), default="manual")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    farmer = relationship("Farmer", back_populates="farms")
    soil_tests = relationship("SoilTest", back_populates="farm", cascade="all, delete-orphan")
    crop_histories = relationship("CropHistory", back_populates="farm", cascade="all, delete-orphan")
    weather_histories = relationship("WeatherHistory", back_populates="farm", cascade="all, delete-orphan")
    disease_records = relationship("DiseaseRecord", back_populates="farm", cascade="all, delete-orphan")
    fertilizer_histories = relationship("FertilizerHistory", back_populates="farm", cascade="all, delete-orphan")
    crop_predictions = relationship("CropPrediction", back_populates="farm", cascade="all, delete-orphan")
    yield_predictions = relationship("YieldPrediction", back_populates="farm", cascade="all, delete-orphan")
    crop_cycles = relationship("CropCycle", back_populates="farm", cascade="all, delete-orphan")


class SoilTest(Base):
    __tablename__ = "soil_tests"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    nitrogen = Column(Float, nullable=False)
    phosphorus = Column(Float, nullable=False)
    potassium = Column(Float, nullable=False)
    ph = Column(Float, nullable=False)
    organic_carbon = Column(Float, default=0.5)
    boron = Column(Float, default=0.2)
    iron = Column(Float, default=4.5)
    zinc = Column(Float, default=0.6)
    measured_at = Column(DateTime, default=datetime.datetime.utcnow)

    farm = relationship("Farm", back_populates="soil_tests")


class CropHistory(Base):
    __tablename__ = "crop_history"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    yield_kg = Column(Float, nullable=False)
    revenue = Column(Float, nullable=True)
    season = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    weather_summary = Column(String(255), nullable=True)
    disease_incidence = Column(String(255), nullable=True)
    fertilizer_used = Column(String(255), nullable=True)
    market_price = Column(Float, nullable=True)
    harvest_date = Column(DateTime, default=datetime.datetime.utcnow)

    farm = relationship("Farm", back_populates="crop_histories")


class WeatherHistory(Base):
    __tablename__ = "weather_histories"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    rainfall = Column(Float, nullable=False)
    wind_speed = Column(Float, default=0.0)
    pressure = Column(Float, default=1013.0)
    uv_index = Column(Float, default=1.0)
    weather_alerts = Column(String(255), nullable=True)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    farm = relationship("Farm", back_populates="weather_histories")


class DiseaseRecord(Base):
    __tablename__ = "disease_records"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(500), nullable=False)
    detected_disease = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)
    severity_level = Column(String(100), nullable=False)
    treatment_plan = Column(Text, nullable=False)
    recovery_time_days = Column(Integer, default=14)
    crop = Column(String(100), nullable=True, default="General")
    model = Column(String(100), nullable=True, default="ConvGeM-NeXt")
    affected_area_ratio = Column(Float, nullable=True, default=0.0)
    affected_percent = Column(Float, nullable=True, default=0.0)
    is_leaf = Column(Boolean, nullable=True, default=True)
    leaf_confidence = Column(Float, nullable=True, default=1.0)
    classification_status = Column(String(100), nullable=True, default="confirmed")
    scanned_at = Column(DateTime, default=datetime.datetime.utcnow)

    farm = relationship("Farm", back_populates="disease_records")


class FertilizerHistory(Base):
    __tablename__ = "fertilizer_history"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    fertilizer_name = Column(String(255), nullable=False)
    dosage_grams_per_sqm = Column(Float, nullable=False)
    organic_alternative_used = Column(Boolean, default=False)
    cost = Column(Float, default=0.0)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow)

    farm = relationship("Farm", back_populates="fertilizer_histories")


class MarketPrices(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    price_today = Column(Float, nullable=False)
    price_forecast_7d = Column(Float, nullable=True)
    price_forecast_30d = Column(Float, nullable=False)
    best_selling_month = Column(String(50), nullable=False)
    demand_trend = Column(String(50), nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class CropPrediction(Base):
    __tablename__ = "crop_predictions"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    recommended_crop = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    expected_yield = Column(Float, nullable=False)
    estimated_profit = Column(Float, nullable=False)
    water_requirement = Column(Float, nullable=False)
    growing_duration_days = Column(Integer, nullable=False)
    disease_risk = Column(String(100), nullable=False)
    market_demand = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    shap_explanation = Column(Text, nullable=False) # Store JSON string of feature impact
    predicted_at = Column(DateTime, default=datetime.datetime.utcnow)

    farm = relationship("Farm", back_populates="crop_predictions")
    recommendation_histories = relationship("RecommendationHistory", back_populates="crop_prediction", cascade="all, delete-orphan")


class YieldPrediction(Base):
    __tablename__ = "yield_predictions"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    predicted_yield_kg = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    expected_harvest_date = Column(DateTime, nullable=False)
    profit_estimate = Column(Float, nullable=False)
    predicted_at = Column(DateTime, default=datetime.datetime.utcnow)

    farm = relationship("Farm", back_populates="yield_predictions")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), nullable=False) # e.g. weather, disease, market, reminder, system
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    farmer = relationship("Farmer", back_populates="notifications")


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id = Column(Integer, primary_key=True, index=True)
    crop_prediction_id = Column(Integer, ForeignKey("crop_predictions.id", ondelete="CASCADE"), nullable=False)
    rating_1_to_5 = Column(Integer, nullable=False)
    farmer_comment = Column(Text, nullable=True)
    actual_outcome = Column(String(100), nullable=True, default="pending") # successful, unsuccessful, pending
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    crop_prediction = relationship("CropPrediction", back_populates="recommendation_histories")


class CropCycle(Base):
    __tablename__ = "crop_cycles"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    season = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    harvest_date = Column(DateTime, nullable=True)
    area_acres = Column(Float, default=1.0)
    
    # Expected vs Actual Yields
    expected_yield = Column(Float, nullable=False)
    actual_yield = Column(Float, nullable=True)
    
    # Expected vs Actual Revenue/Profit
    expected_revenue = Column(Float, nullable=False)
    actual_revenue = Column(Float, nullable=True)
    expected_profit = Column(Float, nullable=False)
    actual_profit = Column(Float, nullable=True)
    
    # Costs & Selling Price
    actual_selling_price = Column(Float, nullable=True)
    cultivation_cost = Column(Float, nullable=True)
    
    # Dynamic events logged during cycle
    fertilizer_used = Column(String(255), nullable=True)
    disease_incidence = Column(String(255), nullable=True)
    
    status = Column(String(50), default="ACTIVE") # ACTIVE, HARVESTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    farm = relationship("Farm", back_populates="crop_cycles")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False) # e.g. fertilizer_model, market_model
    version = Column(String(50), nullable=False)
    training_date = Column(DateTime, default=datetime.datetime.utcnow)
    dataset_version = Column(String(100), nullable=False)
    training_records_count = Column(Integer, default=0)
    validation_metric_name = Column(String(50), nullable=False) # accuracy, r2
    validation_metric_value = Column(Float, nullable=False)
    test_metric_value = Column(Float, nullable=True)
    is_active = Column(Boolean, default=False)



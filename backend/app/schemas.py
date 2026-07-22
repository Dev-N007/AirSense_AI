from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# AQI schemas
class AQIReadingBase(BaseModel):
    station_name: str
    timestamp: datetime
    pm25: float
    pm10: float
    no2: float
    so2: float
    co: float
    o3: float
    aqi: int
    latitude: float
    longitude: float

class AQIReadingCreate(AQIReadingBase):
    pass

class AQIReadingResponse(AQIReadingBase):
    id: int
    class Config:
        from_attributes = True

# Weather schemas
class WeatherDataBase(BaseModel):
    timestamp: datetime
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: float
    precipitation: float

class WeatherDataCreate(WeatherDataBase):
    pass

class WeatherDataResponse(WeatherDataBase):
    id: int
    class Config:
        from_attributes = True

# Geospatial schemas
class GeospatialFeatureBase(BaseModel):
    feature_type: str
    name: str
    latitude: float
    longitude: float

class GeospatialFeatureResponse(GeospatialFeatureBase):
    id: int
    class Config:
        from_attributes = True

# Prediction Request schema
class PredictionRequest(BaseModel):
    station_name: str
    # Recent inputs to compute lag and rolling features
    recent_readings: List[AQIReadingBase] = Field(..., description="Chronological sequence of recent readings (at least 48 hours is recommended).")
    current_weather: WeatherDataBase
    forecasted_weather_24h: WeatherDataBase
    forecasted_weather_48h: WeatherDataBase
    forecasted_weather_72h: WeatherDataBase
    s5p_no2_column: float = Field(0.00015, description="Sentinel-5P NO2 column density")
    s5p_co_column: float = Field(0.045, description="Sentinel-5P CO column density")
    s5p_so2_column: float = Field(0.0002, description="Sentinel-5P SO2 column density")

# SHAP contribution schema
class SHAPContribution(BaseModel):
    feature: str
    value: float
    shap_value: float

# Prediction Response schema
class PredictionResponse(BaseModel):
    station_name: str
    predicted_aqi_24h: int
    predicted_aqi_48h: int
    predicted_aqi_72h: int
    confidence_score: float
    shap_explanations: List[SHAPContribution]
    recommendations: str
    citizen_advisory_en: str
    citizen_advisory_hi: str
    timestamp: datetime

# Map Response schemas
class StationAQI(BaseModel):
    station_name: str
    latitude: float
    longitude: float
    current_aqi: int
    pm25: float
    pm10: float
    timestamp: datetime

class MapDataResponse(BaseModel):
    stations: List[StationAQI]
    features: List[GeospatialFeatureResponse]
    hotspots: List[Dict[str, Any]]

from sqlalchemy import Column, Integer, Float, String, DateTime, Text, JSON
from backend.app.database import Base
import datetime

class AQIReading(Base):
    __tablename__ = "aqi_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    station_name = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    pm25 = Column(Float)
    pm10 = Column(Float)
    no2 = Column(Float)
    so2 = Column(Float)
    co = Column(Float)
    o3 = Column(Float)
    aqi = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)

class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    precipitation = Column(Float)

class GeospatialFeature(Base):
    __tablename__ = "geospatial_features"
    
    id = Column(Integer, primary_key=True, index=True)
    feature_type = Column(String, index=True)  # hospital, school, industrial, road
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)

class PredictionRecord(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    station_name = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    predicted_aqi_24h = Column(Float)
    predicted_aqi_48h = Column(Float)
    predicted_aqi_72h = Column(Float)
    confidence_score = Column(Float)
    shap_explanation = Column(JSON)  # Dict mapping feature -> SHAP value
    recommendations = Column(Text)  # Admin recommendation (Gemini)
    citizen_advisory_en = Column(Text)  # Citizen advisory EN
    citizen_advisory_hi = Column(Text)  # Citizen advisory HI

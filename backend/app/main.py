import os
import json
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from backend.app.config import settings
from backend.app.database import engine, Base, get_db
from backend.app.models import AQIReading, WeatherData, GeospatialFeature, PredictionRecord
from backend.app.schemas import (
    PredictionRequest, PredictionResponse, MapDataResponse, 
    AQIReadingResponse, StationAQI, GeospatialFeatureResponse, SHAPContribution
)
from backend.app.agents.forecast_agent import ForecastAgent
from backend.app.agents.analysis_agent import AnalysisAgent
from backend.app.agents.advisory_agent import AdvisoryAgent

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Delhi Air Quality Intelligence Platform Backend API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Supports both localhost and Vercel deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
forecast_agent = ForecastAgent()
analysis_agent = AnalysisAgent()
advisory_agent = AdvisoryAgent()

@app.on_event("startup")
def seed_database():
    db = next(get_db())
    try:
        # Check if database is already seeded
        if db.query(AQIReading).count() > 0:
            print("Database already contains data. Skipping seeding.")
            return
            
        print("Database is empty. Starting database seeding from real Delhi datasets...")
        merged_path = "data/processed/merged_delhi_aqi.csv"
        osm_path = "data/raw/osm_features.csv"
        
        if not os.path.exists(merged_path) or not os.path.exists(osm_path):
            print("Warning: Processed datasets are missing. Run data collection first.")
            return
            
        # 1. Seed Geospatial Features
        print("Seeding geospatial features from OSM data...")
        df_osm = pd.read_csv(osm_path)
        geo_features = []
        for _, row in df_osm.head(1500).iterrows(): # Limit to top 1500 features to prevent DB bloat
            geo_features.append(GeospatialFeature(
                feature_type=row["feature_type"],
                name=row["name"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"])
            ))
        db.bulk_save_objects(geo_features)
        db.commit()
        print(f"Seeded {len(geo_features)} OSM features.")
        
        # 2. Seed AQI Readings & Weather data
        print("Seeding historical CPCB station readings and weather data...")
        df_merged = pd.read_csv(merged_path)
        df_merged["timestamp"] = pd.to_datetime(df_merged["timestamp"])
        
        # We take a sample of the last 15 days of hourly records to keep database query times snappy
        max_date = df_merged["timestamp"].max()
        start_date = max_date - timedelta(days=15)
        df_recent = df_merged[df_merged["timestamp"] >= start_date]
        
        readings = []
        weather_records = {}
        
        for _, row in df_recent.iterrows():
            ts = row["timestamp"].to_pydatetime()
            
            # Collect unique weather records per timestamp
            ts_str = ts.isoformat()
            if ts_str not in weather_records:
                weather_records[ts_str] = WeatherData(
                    timestamp=ts,
                    temperature=float(row["temperature"]),
                    humidity=float(row["humidity"]),
                    wind_speed=float(row["wind_speed"]),
                    wind_direction=float(row["wind_direction"]),
                    precipitation=float(row["precipitation"])
                )
                
            # Collect ground-station AQI readings
            readings.append(AQIReading(
                station_name=row["station_name"],
                timestamp=ts,
                pm25=float(row["pm25"]),
                pm10=float(row["pm10"]),
                no2=float(row["no2"]),
                so2=float(row["so2"]),
                co=float(row["co"]),
                o3=float(row["o3"]),
                aqi=int(row["aqi"]),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"])
            ))
            
        db.bulk_save_objects(readings)
        db.bulk_save_objects(list(weather_records.values()))
        db.commit()
        
        print(f"Seeded {len(readings)} ground-station hourly records.")
        print(f"Seeded {len(weather_records)} weather hourly slots.")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "AirSense AI",
        "description": "Delhi Urban AQI Intelligence Platform APIs",
        "docs_url": "/docs"
    }

@app.get("/api/history", response_model=List[AQIReadingResponse])
def get_aqi_history(
    station_name: str = Query(..., description="Name of the monitoring station"),
    days: int = Query(7, description="Number of days of history to fetch"),
    db: Session = Depends(get_db)
):
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Since our seeded data timestamp has a fixed range (e.g. 2026-07), 
        # let's fallback to querying the latest records if the cutoff filters out everything.
        latest_reading = db.query(AQIReading).filter(AQIReading.station_name == station_name).order_by(AQIReading.timestamp.desc()).first()
        
        if not latest_reading:
            # Try getting any readings
            readings = db.query(AQIReading).filter(AQIReading.station_name == station_name).order_by(AQIReading.timestamp.asc()).all()
            return readings
            
        max_ts = latest_reading.timestamp
        start_ts = max_ts - timedelta(days=days)
        
        readings = db.query(AQIReading).filter(
            AQIReading.station_name == station_name,
            AQIReading.timestamp >= start_ts
        ).order_by(AQIReading.timestamp.asc()).all()
        
        return readings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/map", response_model=MapDataResponse)
def get_map_data(db: Session = Depends(get_db)):
    try:
        # 1. Fetch latest readings for each station to show active map pins
        subquery = db.query(
            AQIReading.station_name,
            AQIReading.latitude,
            AQIReading.longitude,
            AQIReading.aqi,
            AQIReading.pm25,
            AQIReading.pm10,
            AQIReading.timestamp
        ).order_by(AQIReading.timestamp.desc()).all()
        
        # Filter latest per station manually
        station_map = {}
        for row in subquery:
            if row.station_name not in station_map:
                station_map[row.station_name] = StationAQI(
                    station_name=row.station_name,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    current_aqi=row.aqi,
                    pm25=row.pm25,
                    pm10=row.pm10,
                    timestamp=row.timestamp
                )
                
        stations_list = list(station_map.values())
        
        # 2. Fetch OSM Geospatial landmarks
        features = db.query(GeospatialFeature).all()
        
        # 3. Compute Hotspots (stations with AQI > 250 or top 2 highest AQI)
        hotspots = []
        sorted_stations = sorted(stations_list, key=lambda x: x.current_aqi, reverse=True)
        for idx, s in enumerate(sorted_stations):
            severity = "moderate"
            if s.current_aqi > 300:
                severity = "severe"
            elif s.current_aqi > 200:
                severity = "poor"
                
            if s.current_aqi > 200 or idx < 2:
                hotspots.append({
                    "station_name": s.station_name,
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                    "aqi": s.current_aqi,
                    "severity": severity,
                    "risk_radius_meters": 3000 if severity == "severe" else 2000
                })
                
        return MapDataResponse(
            stations=stations_list,
            features=[GeospatialFeatureResponse(
                id=f.id,
                feature_type=f.feature_type,
                name=f.name,
                latitude=f.latitude,
                longitude=f.longitude
            ) for f in features],
            hotspots=hotspots
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast", response_model=PredictionResponse)
def generate_aqi_forecast(payload: PredictionRequest, db: Session = Depends(get_db)):
    try:
        # Step 1: Execute forecast agent predictions
        payload_dict = payload.dict()
        forecast_res = forecast_agent.predict(payload_dict)
        
        # Step 2: Execute analysis agent to compute SHAP explanations
        shap_attribs = analysis_agent.explain(forecast_res, forecast_agent)
        
        # Step 3: Execute advisory agent to generate admin & citizen advisory
        advisories = advisory_agent.generate_advisory(
            station_name=payload.station_name,
            forecast_data=forecast_res,
            shap_explanations=shap_attribs
        )
        
        # Convert shap contributions to response schemas
        shap_response = [SHAPContribution(
            feature=item["feature"],
            value=item["value"],
            shap_value=item["shap_value"]
        ) for item in shap_attribs]
        
        # Save prediction record to DB
        new_pred = PredictionRecord(
            station_name=payload.station_name,
            predicted_aqi_24h=forecast_res["predicted_aqi_24h"],
            predicted_aqi_48h=forecast_res["predicted_aqi_48h"],
            predicted_aqi_72h=forecast_res["predicted_aqi_72h"],
            confidence_score=forecast_res["confidence_score"],
            shap_explanation={item["feature"]: item["shap_value"] for item in shap_attribs},
            recommendations=advisories["recommendations"],
            citizen_advisory_en=advisories["citizen_advisory_en"],
            citizen_advisory_hi=advisories["citizen_advisory_hi"]
        )
        
        db.add(new_pred)
        db.commit()
        db.refresh(new_pred)
        
        return PredictionResponse(
            station_name=payload.station_name,
            predicted_aqi_24h=new_pred.predicted_aqi_24h,
            predicted_aqi_48h=new_pred.predicted_aqi_48h,
            predicted_aqi_72h=new_pred.predicted_aqi_72h,
            confidence_score=new_pred.confidence_score,
            shap_explanations=shap_response,
            recommendations=new_pred.recommendations,
            citizen_advisory_en=new_pred.citizen_advisory_en,
            citizen_advisory_hi=new_pred.citizen_advisory_hi,
            timestamp=new_pred.timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast pipeline error: {str(e)}")

@app.get("/api/advisory")
def get_latest_advisories(db: Session = Depends(get_db)):
    try:
        # Fetch latest predictions with generated citizen advisories
        records = db.query(PredictionRecord).order_by(PredictionRecord.timestamp.desc()).limit(10).all()
        
        advisories = []
        for r in records:
            # Determine overall alert level from AQI 24h
            aqi = r.predicted_aqi_24h
            alert_level = "Green"
            if aqi > 300: alert_level = "Severe"
            elif aqi > 200: alert_level = "Very Poor"
            elif aqi > 100: alert_level = "Poor"
            
            advisories.append({
                "id": r.id,
                "station_name": r.station_name,
                "predicted_aqi_24h": r.predicted_aqi_24h,
                "alert_level": alert_level,
                "citizen_advisory_en": r.citizen_advisory_en,
                "citizen_advisory_hi": r.citizen_advisory_hi,
                "recommendations": r.recommendations,
                "timestamp": r.timestamp
            })
            
        return advisories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

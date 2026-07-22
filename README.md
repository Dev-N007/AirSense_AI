# AirSense AI 🍃
> **Predict. Explain. Act.**
> An AI-Powered Urban Air Quality Intelligence Platform for Delhi. Built for **ET AI Hackathon 2026 – Problem Statement 5**.

---

## 📋 Table of Contents
1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [Architecture & Data Flow](#-architecture--data-flow)
4. [Folder Structure](#-folder-structure)
5. [Dataset Sources](#-dataset-sources)
6. [Machine Learning Pipeline](#-machine-learning-pipeline)
7. [Multi-Agent Workflow](#-multi-agent-workflow)
8. [Setup & Execution](#-setup--execution)

---

## 🌟 Overview
**AirSense AI** is a state-of-the-art full-stack platform designed to help Delhi city administrators predict, understand, and mitigate urban air pollution. 

Typical air quality models provide predictions but lack explainability. AirSense AI addresses this by combining **LightGBM time-series forecasting** with **SHAP (SHapley Additive exPlanations)** and **Geospatial AI**, using **Gemini 2.5 Flash** to generate automated, context-aware administrative interventions and multilingual citizen advisories.

---

## ⚡ Key Features
- **Dynamic 3-Day Forecast**: Predicts AQI for 24h, 48h, and 72h horizons using independent LightGBM regressors to prevent error propagation.
- **SHAP Explainability**: Details *why* the AQI is changing, showing feature attribution (wind vectors, lag pollutants, nearby industrial/traffic features).
- **Interactive Geospatial Map**: Leaflet-based map of Delhi displaying CPCB stations (color-coded by AQI), spatial hotspots, and toggles for roads, schools, hospitals, industrial areas, and satellite NO2 density.
- **Administrative Recommendations**: Evidence-based mitigation plans (e.g. Graded Response Action Plan - GRAP) automatically compiled using Gemini 2.5 Flash.
- **Multilingual Citizen Advisory**: Public health alerts generated in both English and Hindi.

---

## 🏗️ Architecture & Data Flow

### System Architecture
```
                     +---------------------------------------+
                     |          Next.js Frontend             |
                     | (Dashboard, Charts, Leaflet Map, UI)  |
                     +-------------------+-----------^-------+
                                         |           |
                                    REST |           | API
                                 Payload |           | JSON
                                         v           |
                     +-------------------+-----------+-------+
                     |           FastAPI Backend             |
                     |  (Main Server Routing & App Context)  |
                     +-----+-------------------+-------^-----+
                           |                   |       |
                           | SQLAlchemy        |       | Invoke Agents
                           v                   v       |
  +------------------------+---+  +------------+-------+-----+
  |   Supabase PostgreSQL DB   |  |   Multi-Agent Workflow   |
  |  (Fallback: Local SQLite)  |  |                          |
  |  - ground-station readings |  | 1. Forecast Agent (ML)   |
  |  - weather, spatial records |  | 2. Analysis Agent (SHAP) |
  |  - inference history       |  | 3. Advisory Agent (LLM)  |
  +----------------------------+  +------------+-------------+
                                               |
                                               v Gemini API
                                  +------------+-------------+
                                  |    Gemini 2.5 Flash      |
                                  | (Structured JSON Schema) |
                                  +--------------------------+
```

### Data Flow Diagram
1. **Ingestion**: Ground measurements (OpenAQ/CPCB), historical weather (Open-Meteo), satellite columns (Sentinel-5P CDSE), and OSM layers are fetched and merged by date and coordinates.
2. **Spatial Engineering**: Haversine distance from CPCB stations to nearest road, hospital, school, and industrial zone is calculated.
3. **Training**: Features (lags, rolling averages, wind vectors, spatial, satellite) are compiled and models are trained.
4. **Inference Loop**:
   - Backend queries SQL for recent 48h station readings + weather forecasts.
   - **Forecast Agent** executes LightGBM models for 24/48/72h.
   - **Analysis Agent** runs SHAP TreeExplainer on the feature vector.
   - **Advisory Agent** sends forecast + SHAP + spatial context to **Gemini 2.5 Flash** to get structured interventions and bilingual citizen advisories.
   - Result is saved to the DB and served to the Next.js client.

---

## 📂 Folder Structure
```
AirSense AI/
├── airsense_end_to_end_pipeline.ipynb  # End-to-end ML notebook
├── data/
│   ├── raw/                            # Ingested datasets (OpenAQ, Meteo, OSM, Sentinel)
│   └── processed/                      # Cleaned merged training dataset
├── scripts/
│   ├── download_openaq.py              # OpenAQ downloader
│   ├── download_cpcb.py                # CPCB station distributor
│   ├── download_openmeteo.py           # Weather downloader
│   ├── download_sentinel.py            # Sentinel-5P satellite data script
│   ├── download_osm.py                 # OSM Overpass downloader
│   ├── merge_datasets.py               # Dataset alignment and haversine calculations
│   └── train_models.py                 # Standalone LightGBM training script
├── backend/
│   ├── requirements.txt                # Backend dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI entry point & DB seeder
│   │   ├── config.py                   # Environment configuration
│   │   ├── database.py                 # SQLAlchemy connection manager
│   │   ├── models.py                   # SQLAlchemy tables
│   │   ├── schemas.py                  # Pydantic validation schemas
│   │   └── agents/
│   │       ├── __init__.py
│   │       ├── forecast_agent.py       # LightGBM forecaster agent
│   │       ├── analysis_agent.py       # SHAP explanation agent
│   │       └── advisory_agent.py       # Gemini 2.5 Flash advisory agent
│   └── trained_models/
│       ├── lgbm_aqi_24h.txt            # 24h model weights
│       ├── lgbm_aqi_48h.txt            # 48h model weights
│       ├── lgbm_aqi_72h.txt            # 72h model weights
│       └── model_metadata.json         # Feature list & training dates
└── frontend/
    ├── package.json                    # Frontend dependencies
    └── src/
        ├── app/                        # Next.js App Router pages
        │   ├── layout.tsx
        │   ├── page.tsx                # Dashboard
        │   ├── forecast/page.tsx       # Forecast & SHAP charts
        │   ├── map/page.tsx            # Leaflet Geospatial map
        │   ├── recommendations/page.tsx# Administrative Recommendations
        │   └── advisory/page.tsx       # Multilingual Citizen Advisory
        ├── components/                 # UI components
        └── lib/                        # Utility functions
```

---

## 📊 Dataset Sources
- **AQI / PM2.5 / PM10**: Ground measurements fetched via [OpenAQ](https://openaq.org) aggregating CPCB CAAQMS stations in Delhi.
- **Weather**: Hourly temperature, humidity, precipitation, wind speed, and direction fetched via [Open-Meteo Historical API](https://open-meteo.com).
- **Satellite Columns**: Tropospheric $NO_2$, $CO$, and $SO_2$ densities sourced from Copernicus Sentinel-5P TROPOMI Level 2 atmospheric products.
- **Geospatial Features**: Roads, schools, hospitals, and industrial centers fetched via OpenStreetMap Overpass API interpreter.

---

## 🤖 Machine Learning Pipeline
Our predictive models are trained on real hourly Delhi data spanning 2024-2026:
- **Feature Engineering**: Decomposes wind speed/direction into wind vectors `wind_u` and `wind_v`. Calculates lags (1, 2, 24, 48 hours) and rolling stats (means and standard deviations for 6, 12, and 24 hours). Computes spatial distance vectors from stations to OSM targets.
- **Model**: Three independent **LightGBM Regressors** optimized for tabular time series.
- **Chronological Split**: Trains on 85% of early historical values, testing on the last 15% to replicate real-world deployment.
- **Explainability**: TreeExplainer computes SHAP attributions, outputting exact quantitative contributions per feature.

---

## 👥 Multi-Agent Workflow
1. **Forecast Agent**: Loads booster models, parses the API payload, calculates circular wind vectors, looks up spatial feature distances, builds the feature record, and runs inference.
2. **Analysis Agent**: Executes SHAP TreeExplainer on the feature vector, outputting ranked features by absolute contribution.
3. **Advisory Agent**: Feeds prediction values, SHAP attributions, and local station context to **Gemini 2.5 Flash**, returning structured JSON containing policy guidelines and bilingual citizen bulletins.

---

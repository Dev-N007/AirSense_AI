import os
import json
import pandas as pd
import numpy as np
import lightgbm as lgb
from backend.app.config import settings

class ForecastAgent:
    def __init__(self):
        self.models = {}
        self.metadata = {}
        self.osm_features_df = None
        self.load_models()
        self.load_osm_cache()
        
    def load_models(self):
        model_dir = settings.MODEL_DIR
        print(f"Forecast Agent loading models from: {model_dir}")
        try:
            self.models["24h"] = lgb.Booster(model_file=os.path.join(model_dir, "lgbm_aqi_24h.txt"))
            self.models["48h"] = lgb.Booster(model_file=os.path.join(model_dir, "lgbm_aqi_48h.txt"))
            self.models["72h"] = lgb.Booster(model_file=os.path.join(model_dir, "lgbm_aqi_72h.txt"))
            
            with open(os.path.join(model_dir, "model_metadata.json"), "r") as f:
                self.metadata = json.load(f)
            print("Forecast models loaded successfully.")
        except Exception as e:
            print(f"Warning: Models could not be loaded (yet): {e}")
            
    def load_osm_cache(self):
        # We load OSM features if they exist to support on-the-fly distance computations
        osm_path = "data/raw/osm_features.csv"
        if os.path.exists(osm_path):
            self.osm_features_df = pd.read_csv(osm_path)
            
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
        return R * 2.0 * np.arcsin(np.sqrt(a))
        
    def calculate_station_distances(self, lat, lon):
        distances = {}
        if self.osm_features_df is None or len(self.osm_features_df) == 0:
            return {
                "dist_to_hospital_km": 2.5,
                "dist_to_school_km": 1.2,
                "dist_to_industrial_km": 4.8,
                "dist_to_road_km": 0.5
            }
            
        for feat_type in ["hospital", "school", "industrial", "road"]:
            feat_subset = self.osm_features_df[self.osm_features_df["feature_type"] == feat_type]
            if len(feat_subset) == 0:
                distances[f"dist_to_{feat_type}_km"] = 5.0
                continue
            dists = self.haversine_distance(lat, lon, feat_subset["latitude"].values, feat_subset["longitude"].values)
            distances[f"dist_to_{feat_type}_km"] = np.min(dists)
            
        return distances

    def compile_features(self, request_data: dict) -> pd.DataFrame:
        # Extrapolate lags and rolling features from historical readings
        readings = pd.DataFrame(request_data["recent_readings"])
        readings["timestamp"] = pd.to_datetime(readings["timestamp"])
        readings = readings.sort_values("timestamp")
        
        # Last reading represents current state (t = 0)
        curr_reading = readings.iloc[-1]
        lat = curr_reading["latitude"]
        lon = curr_reading["longitude"]
        
        # Compute OSM distances
        spatial_dists = self.calculate_station_distances(lat, lon)
        
        # We need to construct a single feature row matching the columns of model_metadata
        feature_dict = {
            "latitude": lat,
            "longitude": lon,
            "pm25": curr_reading["pm25"],
            "pm10": curr_reading["pm10"],
            "no2": curr_reading["no2"],
            "so2": curr_reading["so2"],
            "co": curr_reading["co"],
            "o3": curr_reading["o3"],
            
            # Weather variables at t = 0
            "temperature": request_data["current_weather"]["temperature"],
            "humidity": request_data["current_weather"]["humidity"],
            "wind_speed": request_data["current_weather"]["wind_speed"],
            "precipitation": request_data["current_weather"]["precipitation"],
            
            # Satellite variables
            "s5p_no2_column": request_data.get("s5p_no2_column", 0.00015),
            "s5p_co_column": request_data.get("s5p_co_column", 0.045),
            "s5p_so2_column": request_data.get("s5p_so2_column", 0.0002),
        }
        
        # Add spatial distances
        feature_dict.update(spatial_dists)
        
        # Wind U/V components
        rads = np.radians(request_data["current_weather"]["wind_direction"])
        feature_dict["wind_u"] = request_data["current_weather"]["wind_speed"] * np.cos(rads)
        feature_dict["wind_v"] = request_data["current_weather"]["wind_speed"] * np.sin(rads)
        
        # Add target temporal properties
        # For predicting 24h ahead, we can use target timestamp temporal properties
        target_time = pd.to_datetime(request_data["current_weather"]["timestamp"]) + pd.Timedelta(hours=24)
        feature_dict["hour"] = target_time.hour
        feature_dict["day_of_week"] = target_time.dayofweek
        feature_dict["month"] = target_time.month
        feature_dict["is_weekend"] = 1 if target_time.dayofweek >= 5 else 0
        
        # Calculate Lags (t-1, t-2, t-24, t-48 relative to last timestamp in readings)
        # Note: readings is sorted in ascending order.
        # readings.iloc[-1] is t=0, readings.iloc[-2] is t-1 (usually 1 hour before), etc.
        # Let's write robust index checks:
        def get_lag_val(col_name, lag_hrs):
            # Check by index distance assuming hourly frequency
            if len(readings) >= lag_hrs:
                return readings.iloc[-lag_hrs][col_name]
            return curr_reading[col_name]  # Fallback to current
            
        feature_dict["aqi_lag_1"] = get_lag_val("aqi", 1)
        feature_dict["aqi_lag_2"] = get_lag_val("aqi", 2)
        feature_dict["aqi_lag_24"] = get_lag_val("aqi", 24)
        feature_dict["aqi_lag_48"] = get_lag_val("aqi", 48)
        
        feature_dict["pm25_lag_1"] = get_lag_val("pm25", 1)
        feature_dict["pm25_lag_2"] = get_lag_val("pm25", 2)
        feature_dict["pm25_lag_24"] = get_lag_val("pm25", 24)
        feature_dict["pm25_lag_48"] = get_lag_val("pm25", 48)
        
        feature_dict["no2_lag_1"] = get_lag_val("no2", 1)
        feature_dict["no2_lag_2"] = get_lag_val("no2", 2)
        feature_dict["no2_lag_24"] = get_lag_val("no2", 24)
        feature_dict["no2_lag_48"] = get_lag_val("no2", 48)
        
        # Calculate Rolling features
        def get_rolling_stats(col_name, window_size):
            vals = readings[col_name].values[-window_size:]
            return np.mean(vals), np.std(vals) if len(vals) > 1 else 0.0
            
        for col in ["aqi", "pm25"]:
            for window in [6, 12, 24]:
                mean_val, std_val = get_rolling_stats(col, window)
                feature_dict[f"{col}_roll_mean_{window}"] = mean_val
                feature_dict[f"{col}_roll_std_{window}"] = std_val
                
        # Make DataFrame
        df_feats = pd.DataFrame([feature_dict])
        
        # Align column order with metadata features list
        model_features = self.metadata.get("features", list(feature_dict.keys()))
        return df_feats[model_features]

    def predict(self, request_payload: dict) -> dict:
        # Load models if not loaded yet (lazy load fallback)
        if not self.models:
            self.load_models()
            
        if not self.models:
            raise RuntimeError("Forecast Agent: LightGBM models are not trained or missing.")
            
        X = self.compile_features(request_payload)
        
        pred_24 = self.models["24h"].predict(X)[0]
        pred_48 = self.models["48h"].predict(X)[0]
        pred_72 = self.models["72h"].predict(X)[0]
        
        # Apply bounds to match real-world AQI boundaries (0-500)
        pred_24_val = int(np.clip(pred_24, 0, 500))
        pred_48_val = int(np.clip(pred_48, 0, 500))
        pred_72_val = int(np.clip(pred_72, 0, 500))
        
        # Confidence score calculation based on forecasting horizon uncertainty
        # Typically, uncertainty increases over time. We calculate a heuristic confidence score:
        # base confidence on input data variance and horizon
        recent_aqis = [r["aqi"] for r in request_payload["recent_readings"]]
        aqi_variance = np.std(recent_aqis) if len(recent_aqis) > 1 else 10.0
        
        # Higher variance in the past 24h means less confidence
        confidence_base = max(0.4, 1.0 - (aqi_variance / 150.0))
        
        return {
            "predicted_aqi_24h": pred_24_val,
            "predicted_aqi_48h": pred_48_val,
            "predicted_aqi_72h": pred_72_val,
            "confidence_score": round(confidence_base, 2),
            "feature_vector": X
        }

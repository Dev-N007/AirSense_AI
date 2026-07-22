import os
import json
import pandas as pd
import numpy as np
import lightgbm as lgb
from datetime import datetime
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def train_aqi_models():
    print("Loading merged dataset for training...")
    df = pd.read_csv("data/processed/merged_delhi_aqi.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    print(f"Data shape: {df.shape}")
    
    print("Engineering features...")
    # 1. Date/Time Features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # 2. Wind U and V Vectors
    rads = np.radians(df['wind_direction'])
    df['wind_u'] = df['wind_speed'] * np.cos(rads)
    df['wind_v'] = df['wind_speed'] * np.sin(rads)
    
    # 3. Lag Features (AQI, PM2.5, NO2)
    for col in ['aqi', 'pm25', 'no2']:
        for lag in [1, 2, 24, 48]:
            df[f'{col}_lag_{lag}'] = df.groupby('station_name')[col].shift(lag)
            
    # 4. Rolling Features
    for col in ['aqi', 'pm25']:
        for window in [6, 12, 24]:
            df[f'{col}_roll_mean_{window}'] = df.groupby('station_name')[col].transform(lambda x: x.shift(1).rolling(window).mean())
            df[f'{col}_roll_std_{window}'] = df.groupby('station_name')[col].transform(lambda x: x.shift(1).rolling(window).std())
            
    # 5. Future Targets (24h, 48h, 72h ahead predictions)
    df['target_24h'] = df.groupby('station_name')['aqi'].shift(-24)
    df['target_48h'] = df.groupby('station_name')['aqi'].shift(-48)
    df['target_72h'] = df.groupby('station_name')['aqi'].shift(-72)
    
    df_clean = df.dropna().reset_index(drop=True)
    print(f"Feature matrix ready. Cleaned rows: {len(df_clean)}")
    
    # Feature columns list
    feature_cols = [
        'latitude', 'longitude', 'pm25', 'pm10', 'no2', 'so2', 'co', 'o3',
        'temperature', 'humidity', 'wind_speed', 'wind_u', 'wind_v', 'precipitation',
        's5p_no2_column', 's5p_co_column', 's5p_so2_column',
        'dist_to_hospital_km', 'dist_to_school_km', 'dist_to_industrial_km', 'dist_to_road_km',
        'hour', 'day_of_week', 'month', 'is_weekend',
        'aqi_lag_1', 'aqi_lag_2', 'aqi_lag_24', 'aqi_lag_48',
        'pm25_lag_1', 'pm25_lag_2', 'pm25_lag_24', 'pm25_lag_48',
        'no2_lag_1', 'no2_lag_2', 'no2_lag_24', 'no2_lag_48',
        'aqi_roll_mean_6', 'aqi_roll_std_6', 'aqi_roll_mean_12', 'aqi_roll_std_12', 'aqi_roll_mean_24', 'aqi_roll_std_24',
        'pm25_roll_mean_6', 'pm25_roll_std_6', 'pm25_roll_mean_12', 'pm25_roll_std_12', 'pm25_roll_mean_24', 'pm25_roll_std_24'
    ]
    
    # Chronological Train/Test Split (85% Train, 15% Test)
    split_idx = int(len(df_clean) * 0.85)
    train_df = df_clean.iloc[:split_idx]
    test_df = df_clean.iloc[split_idx:]
    
    X_train, y_train_24h, y_train_48h, y_train_72h = train_df[feature_cols], train_df['target_24h'], train_df['target_48h'], train_df['target_72h']
    X_test, y_test_24h, y_test_48h, y_test_72h = test_df[feature_cols], test_df['target_24h'], test_df['target_48h'], test_df['target_72h']
    
    print(f"Training size: {len(X_train)} | Test size: {len(X_test)}")
    
    lgb_params = {
        'objective': 'regression',
        'metric': 'rmse',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'max_depth': 6,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1
    }
    
    os.makedirs("backend/trained_models", exist_ok=True)
    
    # Train 24h Model
    print("Training 24h model...")
    model_24h = lgb.train(lgb_params, lgb.Dataset(X_train, label=y_train_24h), num_boost_round=150)
    pred_24h = model_24h.predict(X_test)
    print_metrics(y_test_24h, pred_24h, "24h")
    model_24h.save_model("backend/trained_models/lgbm_aqi_24h.txt")
    
    # Train 48h Model
    print("Training 48h model...")
    model_48h = lgb.train(lgb_params, lgb.Dataset(X_train, label=y_train_48h), num_boost_round=150)
    pred_48h = model_48h.predict(X_test)
    print_metrics(y_test_48h, pred_48h, "48h")
    model_48h.save_model("backend/trained_models/lgbm_aqi_48h.txt")
    
    # Train 72h Model
    print("Training 72h model...")
    model_72h = lgb.train(lgb_params, lgb.Dataset(X_train, label=y_train_72h), num_boost_round=150)
    pred_72h = model_72h.predict(X_test)
    print_metrics(y_test_72h, pred_72h, "72h")
    model_72h.save_model("backend/trained_models/lgbm_aqi_72h.txt")
    
    # Save Feature metadata
    metadata = {
        "features": feature_cols,
        "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("backend/trained_models/model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
        
    print("Model training successfully completed and models exported to backend/trained_models/")

def print_metrics(y_true, y_pred, label):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    print(f"[{label}] RMSE: {rmse:.4f} | MAE: {mae:.4f} | R2: {r2:.4f}")

if __name__ == "__main__":
    train_aqi_models()

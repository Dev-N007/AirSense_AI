import os
import requests
import pandas as pd
from datetime import datetime

def download_openmeteo_data(start_date="2024-01-01", end_date="2026-07-01"):
    print("Starting Open-Meteo Weather Data Download for Delhi...")
    # Delhi Coordinates
    lat = 28.6139
    lon = 77.2090
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation",
        "timezone": "Asia/Kolkata"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        hourly_data = data.get("hourly", {})
        times = hourly_data.get("time", [])
        temp = hourly_data.get("temperature_2m", [])
        humidity = hourly_data.get("relative_humidity_2m", [])
        wind_speed = hourly_data.get("wind_speed_10m", [])
        wind_dir = hourly_data.get("wind_direction_10m", [])
        precip = hourly_data.get("precipitation", [])
        
        df = pd.DataFrame({
            "timestamp": pd.to_datetime(times),
            "temperature": temp,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_direction": wind_dir,
            "precipitation": precip
        })
        
        os.makedirs("data/raw", exist_ok=True)
        output_path = "data/raw/openmeteo_delhi.csv"
        df.to_csv(output_path, index=False)
        print(f"Weather data downloaded and saved to: {output_path}")
        print(f"Total records: {len(df)}")
        return df
    except Exception as e:
        print(f"Error fetching data from Open-Meteo: {e}")
        # Create a fallback/cached empty check or log
        raise e

if __name__ == "__main__":
    download_openmeteo_data()

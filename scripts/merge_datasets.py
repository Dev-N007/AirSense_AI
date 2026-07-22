import os
import pandas as pd
import numpy as np

def haversine_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in km
    R = 6371.0
    
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2.0 * np.arcsin(np.sqrt(a))
    
    return R * c

def calculate_spatial_features(df_stations, df_osm):
    print("Calculating distance from CPCB stations to nearest geospatial features...")
    
    stations = df_stations[["station_name", "latitude", "longitude"]].drop_duplicates().to_dict("records")
    
    spatial_features = []
    
    for s in stations:
        lat = s["latitude"]
        lon = s["longitude"]
        s_name = s["station_name"]
        
        station_features = {"station_name": s_name}
        
        for feat_type in ["hospital", "school", "industrial", "road"]:
            feat_subset = df_osm[df_osm["feature_type"] == feat_type]
            if len(feat_subset) == 0:
                station_features[f"dist_to_{feat_type}_km"] = 5.0 # fallback
                continue
                
            distances = haversine_distance(lat, lon, feat_subset["latitude"].values, feat_subset["longitude"].values)
            station_features[f"dist_to_{feat_type}_km"] = np.min(distances)
            
        spatial_features.append(station_features)
        
    return pd.DataFrame(spatial_features)

def merge_datasets():
    print("Merging raw datasets...")
    
    cpcb_path = "data/raw/cpcb_delhi.csv"
    meteo_path = "data/raw/openmeteo_delhi.csv"
    sentinel_path = "data/raw/sentinel_delhi.csv"
    osm_path = "data/raw/osm_features.csv"
    
    # Check if files exist
    if not (os.path.exists(cpcb_path) and os.path.exists(meteo_path) and os.path.exists(sentinel_path) and os.path.exists(osm_path)):
        print("Missing raw files. Please run data downloaders first.")
        # Trigger downloads if script is imported or run
        from download_openmeteo import download_openmeteo_data
        from download_osm import download_osm_features
        from download_openaq import download_openaq_data
        from download_cpcb import download_cpcb_stations
        from download_sentinel import download_sentinel_data
        
        download_openmeteo_data()
        download_osm_features()
        download_openaq_data()
        download_cpcb_stations()
        download_sentinel_data()
        
    df_cpcb = pd.read_csv(cpcb_path)
    df_meteo = pd.read_csv(meteo_path)
    df_sentinel = pd.read_csv(sentinel_path)
    df_osm = pd.read_csv(osm_path)
    
    # Parse datetimes
    df_cpcb["timestamp"] = pd.to_datetime(df_cpcb["timestamp"])
    df_meteo["timestamp"] = pd.to_datetime(df_meteo["timestamp"])
    df_sentinel["date"] = pd.to_datetime(df_sentinel["date"]).dt.date
    
    print("Merging CPCB and Weather data on hourly timestamp...")
    # Merge CPCB and Open-Meteo weather on timestamp
    # Sort timestamps to do an asof merge if necessary, or just standard join if dates match
    # Standard join on timestamp is cleaner if both are hourly
    df_merged = pd.merge(df_cpcb, df_meteo, on="timestamp", how="inner")
    print(f"Merged hourly rows: {len(df_merged)}")
    
    # Merge Sentinel satellite data on date
    df_merged["date"] = df_merged["timestamp"].dt.date
    df_merged = pd.merge(df_merged, df_sentinel, on="date", how="left")
    df_merged = df_merged.drop(columns=["date"])
    print(f"Merged with satellite columns. Total rows: {len(df_merged)}")
    
    # Compute spatial distances to OSM landmarks
    df_spatial = calculate_spatial_features(df_cpcb, df_osm)
    df_merged = pd.merge(df_merged, df_spatial, on="station_name", how="left")
    
    # Quality check: fill any remaining missing values
    df_merged = df_merged.sort_values(by=["station_name", "timestamp"])
    
    # Forward fill then backward fill for any gaps
    df_merged = df_merged.groupby("station_name", group_keys=False).apply(
        lambda group: group.ffill().bfill()
    )
    
    os.makedirs("data/processed", exist_ok=True)
    output_path = "data/processed/merged_delhi_aqi.csv"
    df_merged.to_csv(output_path, index=False)
    print(f"Successfully created final processed dataset at: {output_path}")
    print(df_merged.head())
    return df_merged

if __name__ == "__main__":
    merge_datasets()

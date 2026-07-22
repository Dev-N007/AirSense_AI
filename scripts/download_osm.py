import os
import requests
import pandas as pd

def download_osm_features():
    print("Starting OpenStreetMap Geospatial Feature Download for Delhi...")
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Bounding box for Delhi: (S, W, N, E)
    bbox = "28.40,76.84,28.88,77.35"
    
    query = f"""
    [out:json][timeout:120];
    (
      node["amenity"="hospital"]({bbox});
      way["amenity"="hospital"]({bbox});
      node["amenity"="school"]({bbox});
      way["amenity"="school"]({bbox});
      node["landuse"="industrial"]({bbox});
      way["landuse"="industrial"]({bbox});
      node["highway"~"primary|motorway"]({bbox});
      way["highway"~"primary|motorway"]({bbox});
    );
    out center;
    """
    
    headers = {
        "User-Agent": "AirSenseAI-Hackathon-Client/1.0 (contact@airsense.ai)",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        response = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        elements = data.get("elements", [])
        print(f"Downloaded {len(elements)} elements from OSM.")
        
        features = []
        for el in elements:
            tags = el.get("tags", {})
            
            # Determine type
            feat_type = "unknown"
            if "amenity" in tags:
                feat_type = tags["amenity"]  # school or hospital
            elif "landuse" in tags:
                feat_type = tags["landuse"]  # industrial
            elif "highway" in tags:
                feat_type = "road"
                
            name = tags.get("name", f"Unnamed {feat_type}")
            
            # Extract latitude and longitude
            lat = el.get("lat")
            lon = el.get("lon")
            if lat is None or lon is None:
                center = el.get("center", {})
                lat = center.get("lat")
                lon = center.get("lon")
                
            if lat is not None and lon is not None:
                features.append({
                    "id": el.get("id"),
                    "feature_type": feat_type,
                    "name": name,
                    "latitude": lat,
                    "longitude": lon
                })
                
        df = pd.DataFrame(features)
        os.makedirs("data/raw", exist_ok=True)
        output_path = "data/raw/osm_features.csv"
        df.to_csv(output_path, index=False)
        print(f"OSM geospatial features saved to: {output_path}")
        print(f"Total features parsed: {len(df)}")
        return df
    except Exception as e:
        print(f"Error fetching data from OSM Overpass: {e}")
        # Return empty df or raise
        raise e

if __name__ == "__main__":
    download_osm_features()

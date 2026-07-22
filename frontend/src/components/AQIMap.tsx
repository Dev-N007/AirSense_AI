import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, Circle } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Override default marker icons to prevent broken image references in build compilation
const customIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Helper function to return colors based on AQI values
const getAQIColor = (aqi: number) => {
  if (aqi > 300) return "#9333ea"; // Purple (Severe)
  if (aqi > 200) return "#ef4444"; // Red (Very Poor)
  if (aqi > 100) return "#f59e0b"; // Amber (Poor/Moderate)
  return "#10b981"; // Emerald (Good/Satisfactory)
};

interface AQIMapProps {
  stations: any[];
  features: any[];
  hotspots: any[];
  activeLayers: {
    hospitals: boolean;
    schools: boolean;
    industrial: boolean;
    satellite: boolean;
  };
}

export default function AQIMap({ stations, features, hotspots, activeLayers }: AQIMapProps) {
  // Center of Delhi
  const center: [number, number] = [28.6139, 77.2090];
  
  return (
    <div className="w-full h-full rounded-2xl overflow-hidden border border-slate-800 relative shadow-2xl">
      <MapContainer 
        center={center} 
        zoom={11} 
        scrollWheelZoom={true} 
        className="w-full h-full z-10"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" // Premium dark-styled basemap
        />

        {/* 1. Station circle markers (color-coded by AQI) */}
        {stations.map((s) => (
          <CircleMarker
            key={s.station_name}
            center={[s.latitude, s.longitude]}
            radius={14}
            fillColor={getAQIColor(s.current_aqi)}
            color="#0f172a"
            weight={2}
            fillOpacity={0.85}
          >
            <Popup>
              <div className="text-slate-900 font-sans p-1 text-xs">
                <h4 className="font-bold text-sm">{s.station_name.split(",")[0]}</h4>
                <p className="mt-1 font-semibold">Delhi AQI: <span className="font-bold text-rose-600">{s.current_aqi}</span></p>
                <p className="mt-0.5">PM2.5: {s.pm25} µg/m³</p>
                <p className="mt-0.5">PM10: {s.pm10} µg/m³</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* 2. Hotspots - red rings of risk radius */}
        {hotspots.map((h, idx) => (
          <Circle
            key={`hotspot-${idx}`}
            center={[h.latitude, h.longitude]}
            radius={h.risk_radius_meters}
            pathOptions={{
              color: h.severity === "severe" ? "#9333ea" : "#ef4444",
              fillColor: h.severity === "severe" ? "#9333ea" : "#ef4444",
              fillOpacity: 0.12,
              weight: 1.5,
              dashArray: "4 4"
            }}
          />
        ))}

        {/* 3. Toggleable OSM Spatial features */}
        {features.map((f) => {
          const show = 
            (f.feature_type === "hospital" && activeLayers.hospitals) ||
            (f.feature_type === "school" && activeLayers.schools) ||
            (f.feature_type === "industrial" && activeLayers.industrial);
            
          if (!show) return null;
          
          let emoji = "🏥";
          if (f.feature_type === "school") emoji = "🏫";
          if (f.feature_type === "industrial") emoji = "🏭";

          // Customized mini marker pins for spatial landmarks
          const icon = L.divIcon({
            html: `<div style="font-size: 16px; transform: translate(-50%, -50%);">${emoji}</div>`,
            className: "dummy-icon"
          });
          
          return (
            <Marker 
              key={f.id} 
              position={[f.latitude, f.longitude]} 
              icon={icon}
            >
              <Popup>
                <div className="text-slate-900 font-sans text-xs">
                  <span className="capitalize font-bold text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">{f.feature_type}</span>
                  <p className="font-bold text-sm mt-1">{f.name}</p>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* 4. Satellite Sentinel-5P overlay simulation (semi-transparent heat layer) */}
        {activeLayers.satellite && (
          <Circle
            center={center}
            radius={25000} // Covers entire Delhi basin
            pathOptions={{
              color: "#3b82f6",
              fillColor: "#ef4444",
              fillOpacity: 0.25, // Heat glow
              weight: 0
            }}
          />
        )}

      </MapContainer>
    </div>
  );
}

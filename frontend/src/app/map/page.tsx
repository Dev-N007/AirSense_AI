"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";

// Dynamically import Leaflet map with SSR disabled to prevent Node compilation errors
const AQIMap = dynamic(() => import("@/components/AQIMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[550px] rounded-2xl bg-slate-900/60 border border-slate-800 animate-pulse flex flex-col items-center justify-center gap-3 text-slate-400">
      <span className="text-3xl animate-bounce">🗺️</span>
      <p className="text-sm font-semibold">Loading Geospatial Engine...</p>
    </div>
  )
});

// Fallback coordinate mappings for Delhi stations
const FALLBACK_STATIONS = [
  { station_name: "Anand Vihar, Delhi - CPCB", latitude: 28.6476, longitude: 77.3158, current_aqi: 385, pm25: 320, pm10: 450 },
  { station_name: "R K Puram, Delhi - CPCB", latitude: 28.5648, longitude: 77.1887, current_aqi: 310, pm25: 245, pm10: 360 },
  { station_name: "ITO, Delhi - CPCB", latitude: 28.6316, longitude: 77.2489, current_aqi: 295, pm25: 220, pm10: 330 },
  { station_name: "Punjabi Bagh, Delhi - CPCB", latitude: 28.6683, longitude: 77.1167, current_aqi: 335, pm25: 270, pm10: 390 },
  { station_name: "Mandir Marg, Delhi - CPCB", latitude: 28.6341, longitude: 77.2005, current_aqi: 260, pm25: 195, pm10: 290 },
  { station_name: "Dwarka-Sector 8, Delhi - DPD", latitude: 28.5710, longitude: 77.0719, current_aqi: 280, pm25: 210, pm10: 315 },
  { station_name: "Shadipur, Delhi - CPCB", latitude: 28.6514, longitude: 77.1503, current_aqi: 320, pm25: 255, pm10: 375 },
  { station_name: "Siri Fort, Delhi - CPCB", latitude: 28.5504, longitude: 77.2159, current_aqi: 225, pm25: 165, pm10: 250 }
];

const FALLBACK_FEATURES = [
  { id: 1, feature_type: "hospital", name: "Max Super Speciality Hospital, Patparganj", latitude: 28.6295, longitude: 77.2995 },
  { id: 2, feature_type: "hospital", name: "Safdarjung Hospital, Kidwai Nagar", latitude: 28.5678, longitude: 77.2056 },
  { id: 3, feature_type: "school", name: "Delhi Public School, R K Puram", latitude: 28.5630, longitude: 77.1824 },
  { id: 4, feature_type: "school", name: "Modern School, Barakhamba Road", latitude: 28.6278, longitude: 77.2289 },
  { id: 5, feature_type: "industrial", name: "Okhla Industrial Area Phase 3", latitude: 28.5355, longitude: 77.2715 },
  { id: 6, feature_type: "industrial", name: "Mayapuri Industrial Area Phase 2", latitude: 28.6304, longitude: 77.1265 }
];

const FALLBACK_HOTSPOTS = [
  { station_name: "Anand Vihar, Delhi - CPCB", latitude: 28.6476, longitude: 77.3158, aqi: 385, severity: "severe", risk_radius_meters: 3000 },
  { station_name: "Punjabi Bagh, Delhi - CPCB", latitude: 28.6683, longitude: 77.1167, aqi: 335, severity: "poor", risk_radius_meters: 2000 }
];

export default function MapPage() {
  const [stations, setStations] = useState(FALLBACK_STATIONS);
  const [features, setFeatures] = useState(FALLBACK_FEATURES);
  const [hotspots, setHotspots] = useState(FALLBACK_HOTSPOTS);
  const [apiSource, setApiSource] = useState("Local Simulation Cache");

  // Checkbox active state
  const [activeLayers, setActiveLayers] = useState({
    hospitals: true,
    schools: true,
    industrial: false,
    satellite: false
  });

  useEffect(() => {
    fetch("http://localhost:8000/api/map")
      .then((res) => {
        if (!res.ok) throw new Error("API Offline");
        return res.json();
      })
      .then((data) => {
        if (data.stations && data.stations.length > 0) {
          setStations(data.stations);
          setFeatures(data.features || FALLBACK_FEATURES);
          setHotspots(data.hotspots || FALLBACK_HOTSPOTS);
          setApiSource("Live FastAPI Database & OSM");
        }
      })
      .catch((err) => {
        console.log("Using cached fallback coordinates: ", err.message);
        setApiSource("Local Simulation Cache");
      });
  }, []);

  const toggleLayer = (layer: keyof typeof activeLayers) => {
    setActiveLayers(prev => ({
      ...prev,
      [layer]: !prev[layer]
    }));
  };

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="font-heading font-bold text-3xl text-slate-100">
            Geospatial Hotspot Map
          </h2>
          <p className="text-slate-400 text-sm">
            Delhi spatial grid displaying CPCB monitoring stations, school/hospital sensitive receptors, and satellite NO2 overlays.
          </p>
        </div>
        
        <span className="px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700/60">
          Source: <span className="font-bold text-emerald-400">{apiSource}</span>
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Sidebar Controls */}
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-md space-y-6 flex flex-col justify-between">
          <div>
            <h3 className="font-heading font-bold text-sm text-slate-200 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">
              Geospatial Layers
            </h3>
            
            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer group">
                <input 
                  type="checkbox" 
                  checked={activeLayers.hospitals} 
                  onChange={() => toggleLayer("hospitals")}
                  className="w-4 h-4 rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-0 cursor-pointer"
                />
                <div className="text-xs">
                  <p className="font-semibold text-slate-300 group-hover:text-white transition-colors duration-150">🏥 Hospitals</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Sensitive patient receptors</p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer group">
                <input 
                  type="checkbox" 
                  checked={activeLayers.schools} 
                  onChange={() => toggleLayer("schools")}
                  className="w-4 h-4 rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-0 cursor-pointer"
                />
                <div className="text-xs">
                  <p className="font-semibold text-slate-300 group-hover:text-white transition-colors duration-150">🏫 Schools</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Children protection targets</p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer group">
                <input 
                  type="checkbox" 
                  checked={activeLayers.industrial} 
                  onChange={() => toggleLayer("industrial")}
                  className="w-4 h-4 rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-0 cursor-pointer"
                />
                <div className="text-xs">
                  <p className="font-semibold text-slate-300 group-hover:text-white transition-colors duration-150">🏭 Industrial Zones</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Point emissions chimneys</p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer group">
                <input 
                  type="checkbox" 
                  checked={activeLayers.satellite} 
                  onChange={() => toggleLayer("satellite")}
                  className="w-4 h-4 rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-0 cursor-pointer"
                />
                <div className="text-xs">
                  <p className="font-semibold text-slate-300 group-hover:text-white transition-colors duration-150">🛰️ Sentinel-5P NO2 Layer</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Atmospheric column density</p>
                </div>
              </label>
            </div>
          </div>

          {/* Color Index Legend */}
          <div className="border-t border-slate-800 pt-6">
            <h3 className="font-heading font-bold text-xs text-slate-400 uppercase tracking-wider mb-3">
              AQI Scale (Pins)
            </h3>
            <div className="space-y-2 text-[10px] font-bold">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-emerald-500" />
                <span className="text-slate-300">0 - 100: Good/Satisfactory</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-amber-500" />
                <span className="text-slate-300">101 - 200: Moderate/Poor</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500" />
                <span className="text-slate-300">201 - 300: Very Poor</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-purple-500" />
                <span className="text-slate-300">301 - 500: Severe Emergency</span>
              </div>
            </div>
          </div>
        </div>

        {/* Map Rendering Container */}
        <div className="lg:col-span-3 h-[550px]">
          <AQIMap 
            stations={stations} 
            features={features} 
            hotspots={hotspots}
            activeLayers={activeLayers}
          />
        </div>
      </div>

    </div>
  );
}

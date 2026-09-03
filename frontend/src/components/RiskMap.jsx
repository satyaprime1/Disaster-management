import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Pane } from 'react-leaflet';
import * as L from 'leaflet';
import { Layers, Compass } from 'lucide-react';

// Recenter map helper component
function MapRecenter({ lat, lon }) {
  const map = useMap();
  
  useEffect(() => {
    if (lat && lon) {
      map.setView([lat, lon], 10, {
        animate: true,
        duration: 1.2
      });
    }
  }, [lat, lon, map]);

  return null;
}

export default function RiskMap({ location, searchComponent }) {
  if (!location) return null;
  const { city, latitude, longitude } = location;

  // Layer toggling state
  const [layers, setLayers] = useState({
    baseMap: true,
    floodRisk: true,
    landslideRisk: true,
    satellite: false,
    weather: false
  });

  const toggleLayer = (layerName) => {
    setLayers(prev => ({
      ...prev,
      [layerName]: !prev[layerName]
    }));
  };

  // Custom high-tech light-themed marker pins
  const hazardIcon = L.divIcon({
    html: `
      <div class="relative flex items-center justify-center w-8 h-8">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#1A73A8] opacity-40"></span>
        <span class="relative inline-flex rounded-full h-4 w-4 bg-[#1A73A8] border-2 border-white shadow-md"></span>
      </div>
    `,
    className: 'custom-radar-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });

  return (
    <div className="bg-white border border-[#D9E0E7] shadow-sm relative overflow-hidden flex-1 h-[500px] flex flex-col">
      {/* Top Banner on Map */}
      <div className="bg-[#123B63] px-5 py-3 text-white flex justify-between items-center z-[1000] shrink-0 border-b border-[#D9E0E7]/20">
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-[#1A73A8]" />
          <span className="text-xs font-semibold uppercase tracking-wider">Geospatial Hazard Viewer</span>
        </div>
        <div className="text-xs font-mono opacity-90">
          📍 {city.toUpperCase()} · {latitude.toFixed(4)}° N, {longitude.toFixed(4)}° E
        </div>
      </div>

      <div className="relative flex-1 min-h-0 w-full z-1">
        {/* Leaflet Map */}
        <MapContainer
          center={[latitude, longitude]}
          zoom={10}
          scrollWheelZoom={true}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false} // We will use custom placement if needed, default Leaflet zoom will be bottom-right or styled
        >
          {/* Base Tiles - CartoDB Voyager (Light, Clean) */}
          {layers.baseMap && (
            <TileLayer
    url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    attribution="&copy; OpenStreetMap contributors"
/>
          )}

          {/* Optional visual hazard simulation overlay placeholders */}
          {layers.floodRisk && (
            <Pane name="flood-pane" style={{ zIndex: 400 }}>
              {/* Draw a subtle blue overlay simulation around the marker coordinate */}
              <div className="absolute inset-0 bg-[#1A73A8]/5 pointer-events-none" />
            </Pane>
          )}

          <Marker position={[latitude, longitude]} icon={hazardIcon}>
            <Popup className="custom-popup" position={[latitude, longitude]}>
              <div className="text-[#1F2937] font-sans p-1.5 min-w-[150px]">
                <p className="font-bold text-sm text-[#123B63]">{city}</p>
                <p className="text-xs text-[#667085] mt-1 font-mono">Lat: {latitude.toFixed(5)}</p>
                <p className="text-xs text-[#667085] font-mono">Lon: {longitude.toFixed(5)}</p>
                <div className="mt-2 text-[10px] bg-blue-50 text-[#1A73A8] px-2 py-0.5 rounded font-semibold border border-blue-100 inline-block">
                  Hazards Active
                </div>
              </div>
            </Popup>
          </Marker>
          <MapRecenter lat={latitude} lon={longitude} />
        </MapContainer>

        {/* Floating Google Maps-Style City Search Overlay */}
        <div className="absolute top-4 left-4 z-[999] w-full max-w-sm sm:max-w-md px-4 sm:px-0">
          {searchComponent}
        </div>

        {/* Floating Map Layers Control Panel */}
        <div className="absolute bottom-4 right-4 z-[999] bg-white border border-[#D9E0E7] rounded-lg shadow-lg p-4 w-48 font-sans text-xs">
          <div className="flex items-center gap-1.5 border-b border-[#D9E0E7] pb-2 mb-2 font-semibold text-[#123B63]">
            <Layers className="w-3.5 h-3.5" />
            <span>MAP LAYERS</span>
          </div>
          <div className="space-y-2 text-[#1F2937]">
            <label className="flex items-center gap-2 cursor-pointer hover:text-[#1A73A8]">
              <input
                type="checkbox"
                checked={layers.baseMap}
                onChange={() => toggleLayer('baseMap')}
                className="rounded border-[#D9E0E7] text-[#1A73A8] focus:ring-[#1A73A8] w-3.5 h-3.5"
              />
              <span>Base Map</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-[#1A73A8]">
              <input
                type="checkbox"
                checked={layers.floodRisk}
                onChange={() => toggleLayer('floodRisk')}
                className="rounded border-[#D9E0E7] text-[#1A73A8] focus:ring-[#1A73A8] w-3.5 h-3.5"
              />
              <span>Flood Risk Overlay</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-[#1A73A8]">
              <input
                type="checkbox"
                checked={layers.landslideRisk}
                onChange={() => toggleLayer('landslideRisk')}
                className="rounded border-[#D9E0E7] text-[#1A73A8] focus:ring-[#1A73A8] w-3.5 h-3.5"
              />
              <span>Landslide Susceptibility</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-[#1A73A8]">
              <input
                type="checkbox"
                checked={layers.satellite}
                onChange={() => toggleLayer('satellite')}
                className="rounded border-[#D9E0E7] text-[#1A73A8] focus:ring-[#1A73A8] w-3.5 h-3.5"
              />
              <span>Satellite Multi-Spectral</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-[#1A73A8]">
              <input
                type="checkbox"
                checked={layers.weather}
                onChange={() => toggleLayer('weather')}
                className="rounded border-[#D9E0E7] text-[#1A73A8] focus:ring-[#1A73A8] w-3.5 h-3.5"
              />
              <span>Meteorological radar</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

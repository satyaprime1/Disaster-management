import React from 'react';
import { Thermometer, Droplets, CloudRain, BarChart3, Database } from 'lucide-react';

export default function WeatherPanel({ data }) {
  if (!data) return null;

  const {
    rainfall,
    rainfall_3day,
    rainfall_7day,
    max_hourly_rain,
    temperature,
    humidity,
    soil_moisture,
    pressure
  } = data;

  return (
    <div className="bg-white border border-[#D9E0E7] rounded-lg p-5 shadow-sm flex flex-col justify-between">
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#667085] mb-4 border-b border-[#D9E0E7]/60 pb-2">
          ENVIRONMENTAL & METEOROLOGICAL CONDITIONS
        </h2>

        <div className="space-y-4">
          {/* Main Grid */}
          <div className="grid grid-cols-2 gap-4">
            {/* Temperature */}
            <div className="bg-[#F5F7FA] p-3 rounded border border-[#D9E0E7] flex items-start gap-2.5">
              <Thermometer className="w-5 h-5 text-[#E8A317] shrink-0 mt-0.5" />
              <div>
                <p className="text-[10px] font-semibold text-[#667085] uppercase">Temperature</p>
                <p className="text-lg font-bold text-[#1F2937] font-mono mt-0.5">{temperature?.average}°C</p>
                <div className="flex gap-2 text-[9px] font-mono text-[#667085] mt-0.5">
                  <span>Min: {temperature?.minimum}°</span>
                  <span>Max: {temperature?.maximum}°</span>
                </div>
              </div>
            </div>

            {/* Humidity */}
            <div className="bg-[#F5F7FA] p-3 rounded border border-[#D9E0E7] flex items-start gap-2.5">
              <Droplets className="w-5 h-5 text-[#1A73A8] shrink-0 mt-0.5" />
              <div>
                <p className="text-[10px] font-semibold text-[#667085] uppercase">Humidity</p>
                <p className="text-lg font-bold text-[#1F2937] font-mono mt-0.5">{humidity}%</p>
                <div className="w-16 bg-[#D9E0E7] h-1 rounded-full overflow-hidden mt-2">
                  <div className="bg-[#1A73A8] h-full" style={{ width: `${humidity}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Precipitation Levels */}
          <div className="bg-[#F5F7FA] p-3 rounded border border-[#D9E0E7] space-y-2">
            <div className="flex items-center gap-2 border-b border-[#D9E0E7]/60 pb-1.5">
              <CloudRain className="w-4.5 h-4.5 text-[#123B63]" />
              <span className="text-[10px] font-semibold text-[#123B63] uppercase">Precipitation Accumulation</span>
            </div>
            
            <div className="grid grid-cols-4 gap-2 text-center">
              <div className="bg-white p-2 rounded border border-[#D9E0E7] shadow-sm">
                <p className="text-[8px] font-bold text-[#667085] uppercase">Current</p>
                <p className="text-xs font-bold text-[#1F2937] font-mono mt-0.5">{rainfall} mm</p>
              </div>
              <div className="bg-white p-2 rounded border border-[#D9E0E7] shadow-sm">
                <p className="text-[8px] font-bold text-[#667085] uppercase">Hourly Max</p>
                <p className="text-xs font-bold text-[#1F2937] font-mono mt-0.5">{max_hourly_rain} mm</p>
              </div>
              <div className="bg-white p-2 rounded border border-[#D9E0E7] shadow-sm">
                <p className="text-[8px] font-bold text-[#667085] uppercase">3-Day</p>
                <p className="text-xs font-bold text-[#1F2937] font-mono mt-0.5">{rainfall_3day} mm</p>
              </div>
              <div className="bg-white p-2 rounded border border-[#D9E0E7] shadow-sm">
                <p className="text-[8px] font-bold text-[#667085] uppercase">7-Day</p>
                <p className="text-xs font-bold text-[#1F2937] font-mono mt-0.5">{rainfall_7day} mm</p>
              </div>
            </div>
          </div>

          {/* Soil Moisture */}
          <div className="bg-[#F5F7FA] p-3 rounded border border-[#D9E0E7] space-y-2.5">
            <div className="flex items-center gap-2 border-b border-[#D9E0E7]/60 pb-1.5">
              <Database className="w-4.5 h-4.5 text-[#16845B]" />
              <span className="text-[10px] font-semibold text-[#16845B] uppercase">Soil Moisture Levels</span>
            </div>

            <div className="space-y-2 mt-1">
              <div>
                <div className="flex justify-between text-[9px] font-semibold text-[#667085] mb-1">
                  <span>Surface Level (0 - 7 cm)</span>
                  <span className="font-mono">{Math.round((soil_moisture?.["0_7cm"] || 0) * 100)}%</span>
                </div>
                <div className="w-full bg-[#D9E0E7] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[#16845B] h-full transition-all duration-500"
                    style={{ width: `${(soil_moisture?.["0_7cm"] || 0) * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[9px] font-semibold text-[#667085] mb-1">
                  <span>Subsoil Level (7 - 28 cm)</span>
                  <span className="font-mono">{Math.round((soil_moisture?.["7_28cm"] || 0) * 100)}%</span>
                </div>
                <div className="w-full bg-[#D9E0E7] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[#16845B]/85 h-full transition-all duration-500"
                    style={{ width: `${(soil_moisture?.["7_28cm"] || 0) * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[9px] font-semibold text-[#667085] mb-1">
                  <span>Deep Horizon (28 - 100 cm)</span>
                  <span className="font-mono">{Math.round((soil_moisture?.["28_100cm"] || 0) * 100)}%</span>
                </div>
                <div className="w-full bg-[#D9E0E7] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[#16845B]/70 h-full transition-all duration-500"
                    style={{ width: `${(soil_moisture?.["28_100cm"] || 0) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

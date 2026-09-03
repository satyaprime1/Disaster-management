import React, { useState } from 'react';
import { Cpu, ChevronDown, ChevronUp } from 'lucide-react';

export default function ModelDetails() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-white border border-[#D9E0E7] rounded-lg overflow-hidden shadow-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-[#F5F7FA] transition-colors"
      >
        <div className="flex items-center gap-3">
          <Cpu className="w-5 h-5 text-[#123B63]" />
          <div>
            <h3 className="text-sm font-semibold text-[#123B63]">TECHNICAL MODEL SPECIFICATIONS</h3>
            <p className="text-xs text-[#667085]">View underlying predictive parameters & machine learning pipelines</p>
          </div>
        </div>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-[#667085]" />
        ) : (
          <ChevronDown className="w-5 h-5 text-[#667085]" />
        )}
      </button>

      {isOpen && (
        <div className="border-t border-[#D9E0E7] bg-[#F5F7FA]/40 p-5 space-y-4 text-xs text-[#1F2937] leading-relaxed">
          <div className="space-y-1">
            <h4 className="font-semibold text-[#123B63] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#D93025]"></span>
              Landslide Prediction Pipeline (XGBoost Classifier)
            </h4>
            <p className="pl-3 text-[#667085]">
              Utilizes a gradient boosting algorithm trained on regional digital elevation models (DEM), soil permeability matrices, and dynamic Open-Meteo precipitation indexes. Recalculates risk weights across 14 meteorological inputs.
            </p>
          </div>

          <div className="space-y-1 border-t border-[#D9E0E7] pt-3.5">
            <h4 className="font-semibold text-[#123B63] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#1A73A8]"></span>
              Flood Simulation Pipeline (Random Forest Ensemble)
            </h4>
            <p className="pl-3 text-[#667085]">
              An ensemble decision tree model built on historical rainfall records. Projects water runoff rates based on soil saturation percentages (0-7cm surface, 7-28cm subsoil, 28-100cm deep layers) and 3-day / 7-day cumulative precipitation forecasts.
            </p>
          </div>

          <div className="space-y-1 border-t border-[#D9E0E7] pt-3.5">
            <h4 className="font-semibold text-[#123B63] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#16845B]"></span>
              Satellite Monitoring Pipeline (ResNet50 Deep CNN)
            </h4>
            <p className="pl-3 text-[#667085]">
              Deep Convolutional Neural Network deployed on high-resolution Sentinel-2 image grids. Extracts multi-spectral bands to isolate Normalized Difference Water Index (NDWI) and Normalized Difference Vegetation Index (NDVI) anomaly vectors.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

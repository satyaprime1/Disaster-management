import React from 'react';
import { AlertCircle, CheckCircle, Info } from 'lucide-react';

export default function OverallRisk({ data, location }) {
  const { city, country, latitude, longitude } = location;
  const { risk } = data;

  const getRiskMeta = (riskLevel) => {
    switch (riskLevel) {
      case 'HIGH':
        return {
          icon: <AlertCircle className="w-5 h-5 text-[#D93025]" />,
          text: 'HIGH RISK',
          color: 'text-[#D93025] bg-[#D93025]/10 border-[#D93025]/20',
          dot: 'bg-[#D93025]',
          desc: 'CRITICAL ALERT: Multiple high-severity hazards detected in this region. Review landslide and flood risk factors and follow local disaster management protocols.'
        };
      case 'MODERATE':
        return {
          icon: <Info className="w-5 h-5 text-[#E8A317]" />,
          text: 'MODERATE RISK',
          color: 'text-[#E8A317] bg-[#E8A317]/10 border-[#E8A317]/20',
          dot: 'bg-[#E8A317]',
          desc: 'ADVISORY: Moderate hazard risks detected. Continue monitoring environmental parameters, rainfall thresholds, and regional warnings.'
        };
      case 'LOW':
      default:
        return {
          icon: <CheckCircle className="w-5 h-5 text-[#16845B]" />,
          text: 'LOW / SAFE',
          color: 'text-[#16845B] bg-[#16845B]/10 border-[#16845B]/20',
          dot: 'bg-[#16845B]',
          desc: 'NORMAL STATUS: Environmental conditions are within safe historical thresholds. No active disaster warning levels exist for this location.'
        };
    }
  };

  const meta = getRiskMeta(risk);

  return (
    <div className="bg-white border border-[#D9E0E7] rounded-lg p-5 shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D9E0E7]/60 pb-4 mb-4">
        {/* City and Coordinates Details */}
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-[#667085]">
            SELECTED REGION
          </div>
          <h3 className="text-lg font-bold text-[#123B63] mt-0.5">
            {city}, {country}
          </h3>
          <p className="text-xs font-mono text-[#667085] mt-0.5">
            Coordinates: {latitude.toFixed(5)}° N · {longitude.toFixed(5)}° E
          </p>
        </div>

        {/* Overall Status Banner */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase text-[#667085] hidden md:inline">
            OVERALL RISK ASSESSMENT:
          </span>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded border ${meta.color} font-semibold text-sm`}>
            <span className={`w-2 h-2 rounded-full ${meta.dot} shrink-0`}></span>
            {meta.text}
          </div>
        </div>
      </div>

      <div className="flex items-start gap-3 bg-[#F5F7FA] p-4 rounded border border-[#D9E0E7] text-xs text-[#1F2937] leading-relaxed">
        {meta.icon}
        <div>
          <span className="font-semibold text-[#123B63] block mb-0.5">Situation Report:</span>
          {meta.desc}
        </div>
      </div>
    </div>
  );
}

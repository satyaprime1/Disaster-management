import React from 'react';
import { Waves } from 'lucide-react';

export default function FloodCard({ data }) {
  if (!data) return null;
  const { probability, risk, weather_records } = data;

  const getRiskStyles = (level) => {
    switch (level) {
      case 'HIGH':
        return {
          border: 'border-[#D93025]',
          bgBadge: 'bg-[#D93025]/10 text-[#D93025] border-[#D93025]/20',
          progressBar: 'bg-[#D93025]',
          dot: 'bg-[#D93025]'
        };
      case 'MODERATE':
        return {
          border: 'border-[#E8A317]',
          bgBadge: 'bg-[#E8A317]/10 text-[#E8A317] border-[#E8A317]/20',
          progressBar: 'bg-[#E8A317]',
          dot: 'bg-[#E8A317]'
        };
      case 'LOW':
      default:
        return {
          border: 'border-[#16845B]',
          bgBadge: 'bg-[#16845B]/10 text-[#16845B] border-[#16845B]/20',
          progressBar: 'bg-[#16845B]',
          dot: 'bg-[#16845B]'
        };
    }
  };

  const styles = getRiskStyles(risk);

  return (
    <div className="bg-white border border-[#D9E0E7] rounded-lg p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between border-b border-[#D9E0E7]/60 pb-3 mb-4">
          <div className="flex items-center gap-2 text-[#123B63]">
            <Waves className="w-5 h-5" />
            <span className="text-sm font-semibold tracking-wide">Flood Hazard</span>
          </div>
          <div className={`flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-semibold ${styles.bgBadge}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`}></span>
            {risk}
          </div>
        </div>

        <div className="my-3 text-center">
          <span className="text-3xl font-extrabold text-[#1F2937] tracking-tight">
            {probability.toFixed(2)}%
          </span>
          <p className="text-[10px] text-[#667085] uppercase tracking-wider font-semibold mt-1">
            Probability Index
          </p>
        </div>
      </div>

      <div className="space-y-3.5 mt-2">
        <div>
          <div className="w-full bg-[#F5F7FA] rounded-full h-2 overflow-hidden border border-[#D9E0E7]">
            <div
              className={`h-full ${styles.progressBar} transition-all duration-500`}
              style={{ width: `${probability}%` }}
            />
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-[#D9E0E7]/60 pt-3 text-xs text-[#667085]">
          <span className="font-medium">Weather Data Scope</span>
          <span className="font-mono font-bold text-[#1F2937] bg-[#F5F7FA] px-2 py-0.5 rounded border border-[#D9E0E7]">
            {weather_records} hrs
          </span>
        </div>
      </div>
    </div>
  );
}

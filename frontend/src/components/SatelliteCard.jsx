import React from 'react';
import { Radio } from 'lucide-react';

export default function SatelliteCard({ data }) {
  if (!data) return null;
  const { status, message, predictions } = data;

  const getStatusStyles = (statusVal) => {
    switch (statusVal?.toLowerCase()) {
      case 'active':
      case 'completed':
        return {
          bgBadge: 'bg-emerald-50 text-[#16845B] border-emerald-200',
          dot: 'bg-[#16845B]',
          label: 'Completed'
        };
      case 'error':
        return {
          bgBadge: 'bg-red-50 text-[#D93025] border-red-200',
          dot: 'bg-[#D93025]',
          label: 'Error'
        };
      case 'pending':
      case 'analyzing':
      default:
        return {
          bgBadge: 'bg-blue-50 text-[#1A73A8] border-blue-200 animate-pulse',
          dot: 'bg-[#1A73A8]',
          label: 'Analyzing'
        };
    }
  };

  const styles = getStatusStyles(status);

  return (
    <div className="bg-white border border-[#D9E0E7] rounded-lg p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between border-b border-[#D9E0E7]/60 pb-3 mb-4">
          <div className="flex items-center gap-2 text-[#123B63]">
            <Radio className="w-5 h-5" />
            <span className="text-sm font-semibold tracking-wide">Satellite Analytics</span>
          </div>
          <div className={`flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-semibold ${styles.bgBadge}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`}></span>
            {styles.label}
          </div>
        </div>

        <div className="my-3 text-center">
          <span className="text-xl font-bold text-[#1F2937] tracking-widest font-mono">
            {status === 'pending' ? 'PROCESSING' : status.toUpperCase()}
          </span>
          <p className="text-[10px] text-[#667085] uppercase tracking-wider font-semibold mt-1">
            Sentinel Pipeline Status
          </p>
        </div>
      </div>

      <div className="space-y-3 mt-2">
        <div className="bg-[#F5F7FA] p-3 rounded border border-[#D9E0E7] text-[11px] leading-relaxed text-[#667085]">
          <span className="font-semibold text-[#123B63] block mb-0.5 uppercase text-[9px] tracking-wider">
            Telemetry Feed
          </span>
          {message || 'Awaiting image ingest from Copernicus Sentinel Hub API endpoint. Real-time NDVI/NDWI layers pending.'}
        </div>

        {predictions && predictions.length > 0 && (
          <div className="border-t border-[#D9E0E7]/60 pt-2.5">
            <span className="text-[10px] font-bold text-[#123B63] block mb-1">DETECTION ALERTS</span>
            <div className="space-y-1">
              {predictions.map((p, index) => (
                <div key={index} className="text-xs bg-red-50 text-[#D93025] px-2 py-1 rounded border border-red-100 font-medium">
                  • {p.hazard}: {p.probability}% risk detected
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between border-t border-[#D9E0E7]/60 pt-3 text-xs text-[#667085]">
          <span className="font-medium">Service Stream</span>
          <span className="font-mono font-bold text-[#1F2937] bg-[#F5F7FA] px-2 py-0.5 rounded border border-[#D9E0E7]">
            Copernicus S2
          </span>
        </div>
      </div>
    </div>
  );
}

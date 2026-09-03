import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorMessage({ message, onRetry }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6 shadow-sm flex flex-col items-center text-center max-w-md mx-auto">
      <AlertTriangle className="w-10 h-10 text-[#D93025] mb-3" />
      <h3 className="text-sm font-bold text-[#D93025] uppercase tracking-wider">
        Prediction Pipeline Error
      </h3>
      <p className="text-xs text-[#1F2937] mt-2 leading-relaxed">
        {message || 'We encountered an error while trying to fetch weather and model telemetry for this city. Please try again.'}
      </p>

      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 bg-white border border-[#D9E0E7] hover:border-[#667085] hover:bg-[#F5F7FA] text-[#123B63] px-4 py-2 rounded text-xs font-semibold flex items-center gap-1.5 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Analysis
        </button>
      )}
    </div>
  );
}

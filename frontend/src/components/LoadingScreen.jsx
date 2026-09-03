import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, Circle } from 'lucide-react';

export default function LoadingScreen() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const intervals = [
      setTimeout(() => setStep(1), 300),
      setTimeout(() => setStep(2), 700),
      setTimeout(() => setStep(3), 1100),
      setTimeout(() => setStep(4), 1500)
    ];
    return () => intervals.forEach(clearTimeout);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 bg-white border border-[#D9E0E7] rounded-lg shadow-sm min-h-[350px]">
      <Loader2 className="w-8 h-8 text-[#1A73A8] animate-spin mb-6" />
      
      <div className="text-center mb-6">
        <h3 className="text-sm font-bold text-[#123B63] uppercase tracking-wider">
          Executing Multi-Hazard Predictor
        </h3>
        <p className="text-xs text-[#667085] mt-1">
          Synthesizing local Open-Meteo telemetry & ML weight kernels...
        </p>
      </div>

      <div className="w-full max-w-xs space-y-2.5 font-sans text-xs">
        {/* Step 1 */}
        <div className="flex items-center gap-3">
          {step >= 1 ? (
            <CheckCircle2 className="w-4 h-4 text-[#16845B]" />
          ) : (
            <Loader2 className="w-4 h-4 text-[#1A73A8] animate-spin" />
          )}
          <span className={step >= 1 ? "text-[#1F2937] font-semibold" : "text-[#667085]"}>
            Location geocoded successfully
          </span>
        </div>

        {/* Step 2 */}
        <div className="flex items-center gap-3">
          {step >= 2 ? (
            <CheckCircle2 className="w-4 h-4 text-[#16845B]" />
          ) : step === 1 ? (
            <Loader2 className="w-4 h-4 text-[#1A73A8] animate-spin" />
          ) : (
            <Circle className="w-4 h-4 text-[#D9E0E7]" />
          )}
          <span className={step >= 2 ? "text-[#1F2937] font-semibold" : "text-[#667085]"}>
            Recent meteorological data fetched
          </span>
        </div>

        {/* Step 3 */}
        <div className="flex items-center gap-3">
          {step >= 3 ? (
            <CheckCircle2 className="w-4 h-4 text-[#16845B]" />
          ) : step === 2 ? (
            <Loader2 className="w-4 h-4 text-[#1A73A8] animate-spin" />
          ) : (
            <Circle className="w-4 h-4 text-[#D9E0E7]" />
          )}
          <span className={step >= 3 ? "text-[#1F2937] font-semibold" : "text-[#667085]"}>
            Landslide XGBoost classifier executed
          </span>
        </div>

        {/* Step 4 */}
        <div className="flex items-center gap-3">
          {step >= 4 ? (
            <CheckCircle2 className="w-4 h-4 text-[#16845B]" />
          ) : step === 3 ? (
            <Loader2 className="w-4 h-4 text-[#1A73A8] animate-spin" />
          ) : (
            <Circle className="w-4 h-4 text-[#D9E0E7]" />
          )}
          <span className={step >= 4 ? "text-[#1F2937] font-semibold" : "text-[#667085]"}>
            Flood Random Forest simulation compiled
          </span>
        </div>
      </div>
    </div>
  );
}

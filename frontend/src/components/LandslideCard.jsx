import React from 'react';
import { Mountain } from 'lucide-react';

export default function LandslideCard({ data }) {
  if (!data) return null;

  // ============================================================
  // BACKEND VALUES
  // ============================================================

  const riskScore = Number(data.risk_score ?? 0);
  const riskLevel = data.risk_level ?? 'LOW';

  // Keep progress bar between 0 and 100
  const progressWidth = Math.min(
    Math.max(riskScore, 0),
    100
  );


  // ============================================================
  // RISK STYLES
  // ============================================================

  const getRiskStyles = (level) => {
    switch (level) {

      case 'HIGH':
        return {
          bgBadge:
            'bg-[#D93025]/10 text-[#D93025] border-[#D93025]/20',

          progressBar:
            'bg-[#D93025]',

          dot:
            'bg-[#D93025]'
        };


      case 'MEDIUM':
        return {
          bgBadge:
            'bg-[#E8A317]/10 text-[#E8A317] border-[#E8A317]/20',

          progressBar:
            'bg-[#E8A317]',

          dot:
            'bg-[#E8A317]'
        };


      case 'LOW':
      default:
        return {
          bgBadge:
            'bg-[#16845B]/10 text-[#16845B] border-[#16845B]/20',

          progressBar:
            'bg-[#16845B]',

          dot:
            'bg-[#16845B]'
        };
    }
  };


  const styles = getRiskStyles(
    riskLevel
  );


  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="bg-white border border-[#D9E0E7] rounded-lg p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">

      <div>

        {/* ======================================================
            HEADER
        ====================================================== */}

        <div className="flex items-center justify-between border-b border-[#D9E0E7]/60 pb-3 mb-4">

          <div className="flex items-center gap-2 text-[#123B63]">

            <Mountain className="w-5 h-5" />

            <span className="text-sm font-semibold tracking-wide">
              Landslide Hazard
            </span>

          </div>


          {/* RISK BADGE */}

          <div
            className={`flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-semibold ${styles.bgBadge}`}
          >

            <span
              className={`w-1.5 h-1.5 rounded-full ${styles.dot}`}
            />

            {riskLevel}

          </div>

        </div>


        {/* ======================================================
            RISK SCORE
        ====================================================== */}

        <div className="my-3 text-center">

          <span className="text-3xl font-extrabold text-[#1F2937] tracking-tight">

            {riskScore.toFixed(2)}%

          </span>


          <p className="text-[10px] text-[#667085] uppercase tracking-wider font-semibold mt-1">

            Risk Score

          </p>

        </div>

      </div>


      {/* ========================================================
          PROGRESS BAR
      ======================================================== */}

      <div className="space-y-3.5 mt-2">

        <div>

          <div className="w-full bg-[#F5F7FA] rounded-full h-2 overflow-hidden border border-[#D9E0E7]">

            <div
              className={`h-full ${styles.progressBar} transition-all duration-500`}
              style={{
                width: `${progressWidth}%`
              }}
            />

          </div>

        </div>


        {/* ======================================================
            RISK INFORMATION
        ====================================================== */}

        <div className="flex items-center justify-between border-t border-[#D9E0E7]/60 pt-3 text-xs text-[#667085]">

          <span className="font-medium">
            Environmental Risk Score
          </span>


          <span className="font-mono font-bold text-[#1F2937] bg-[#F5F7FA] px-2 py-0.5 rounded border border-[#D9E0E7]">

            {riskLevel}

          </span>

        </div>

      </div>

    </div>
  );
}
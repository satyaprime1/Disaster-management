import React from 'react';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';

export default function AlertPanel({ result, type, message }) {
  // Simple error message panel
  if (type === 'error' && message) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3 shadow-sm">
        <AlertTriangle className="w-5 h-5 text-[#D93025] shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-semibold text-[#D93025] font-sans">SYSTEM PIPELINE EXCEPTION</h4>
          <p className="text-xs text-[#1F2937] mt-1">{message}</p>
        </div>
      </div>
    );
  }

  if (!result || !result.alerts) return null;
  const { alerts } = result;

  return (
    <div className="bg-white border border-[#D9E0E7] rounded-lg p-5 shadow-sm space-y-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-[#667085] border-b border-[#D9E0E7]/60 pb-2">
        ACTIVE DISASTER ADVISORIES & ALERTS
      </h2>

      {alerts.length === 0 ? (
        <div className="text-xs text-[#667085] py-2 italic">
          No active warnings or advisories for this region.
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert, idx) => {
            const isHigh = alert.severity === 'HIGH';
            const isModerate = alert.severity === 'MODERATE';
            
            let cardBg = 'bg-[#F5F7FA] border-[#D9E0E7]';
            let titleColor = 'text-[#667085]';
            let badgeStyle = 'bg-slate-100 text-slate-700 border-slate-200';
            let bulletColor = 'bg-slate-400';
            let icon = <Info className="w-4 h-4 text-[#667085] mt-0.5 shrink-0" />;

            if (isHigh) {
              cardBg = 'bg-[#D93025]/5 border-[#D93025]/20';
              titleColor = 'text-[#D93025]';
              badgeStyle = 'bg-[#D93025]/10 text-[#D93025] border-[#D93025]/20';
              bulletColor = 'bg-[#D93025]';
              icon = <AlertCircle className="w-4 h-4 text-[#D93025] mt-0.5 shrink-0 animate-pulse" />;
            } else if (isModerate) {
              cardBg = 'bg-[#E8A317]/5 border-[#E8A317]/20';
              titleColor = 'text-[#E8A317]';
              badgeStyle = 'bg-[#E8A317]/10 text-[#E8A317] border-[#E8A317]/20';
              bulletColor = 'bg-[#E8A317]';
              icon = <Info className="w-4 h-4 text-[#E8A317] mt-0.5 shrink-0" />;
            }

            return (
              <div
                key={idx}
                className={`border rounded p-4 flex items-start gap-3 transition-all ${cardBg}`}
              >
                {icon}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-semibold uppercase tracking-wider ${titleColor}`}>
                      {alert.type} Advisory
                    </span>
                    <span className={`text-[9px] font-bold tracking-wider px-1.5 py-0.5 rounded border ${badgeStyle}`}>
                      {alert.severity}
                    </span>
                  </div>
                  <p className="text-xs text-[#1F2937] mt-1.5 leading-relaxed font-sans">
                    {alert.message}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

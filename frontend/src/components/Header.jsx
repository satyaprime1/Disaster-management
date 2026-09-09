import React from "react";

export default function Header({ backendConnected }) {
  return (
    <header className="bg-white border-b border-[#dfe5eb]">
      <div className="max-w-7xl mx-auto px-5 sm:px-6 min-h-[78px] flex items-center justify-between gap-6">
        <div className="flex items-center gap-3">
          <img src="/assets/veyrix-symbol.png" alt="VEYRiX" className="w-12 h-12 object-contain" />
          <div>
            <div className="text-[22px] font-bold tracking-[0.08em] text-[#123f66]">VEYRiX</div>
            <p className="text-[10px] uppercase tracking-[0.08em] text-[#6b7785] mt-1">
              Multi-Hazard Prediction &amp; Monitoring System
            </p>
          </div>
        </div>
        <div className="text-xs text-[#5f6b78]">
          {backendConnected ? "System connected" : "System offline"}
        </div>
      </div>
    </header>
  );
}

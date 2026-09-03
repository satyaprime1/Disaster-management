import React from 'react';

export default function HazardCards({ children }) {
  return (
    <div className="space-y-3">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-[#667085]">
        DETAILED HAZARD ANALYSIS
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {children}
      </div>
    </div>
  );
}

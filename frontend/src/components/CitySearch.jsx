import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

export default function CitySearch({ onAnalyze, loading }) {
  const [city, setCity] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (city.trim()) {
      onAnalyze(city.trim());
    }
  };

  const handleSuggestionClick = (suggestedCity) => {
    setCity(suggestedCity);
    onAnalyze(suggestedCity);
  };

  const suggestions = ["Hyderabad", "Mumbai", "Gangtok", "Shimla", "New Delhi"];

  return (
    <div className="bg-white border border-[#D9E0E7] rounded-lg p-5 shadow-sm">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-[#667085] mb-3">
        SELECT LOCATION FOR ANALYSIS
      </h2>

      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#667085]">
            <Search className="w-5 h-5" />
          </span>
          <input
            type="text"
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#D9E0E7] rounded text-[#1F2937] placeholder-[#667085] focus:outline-none focus:border-[#1A73A8] focus:ring-1 focus:ring-[#1A73A8] transition-all font-sans text-sm"
            placeholder="Search city or coordinates..."
            value={city}
            onChange={(e) => setCity(e.target.value)}
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !city.trim()}
          className="bg-[#1A73A8] hover:bg-[#123B63] disabled:bg-[#F5F7FA] disabled:text-[#667085] text-white font-semibold font-sans tracking-wide px-6 py-2.5 rounded border border-[#1A73A8] hover:border-[#123B63] transition-all flex items-center justify-center gap-2 text-sm"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              ANALYZING...
            </>
          ) : (
            'ANALYZE'
          )}
        </button>
      </form>

      <div className="mt-3.5 flex flex-wrap items-center gap-2 border-t border-[#D9E0E7]/60 pt-3">
        <span className="text-xs text-[#667085] font-medium">Quick Select:</span>
        {suggestions.map((suggestedCity) => (
          <button
            key={suggestedCity}
            type="button"
            onClick={() => handleSuggestionClick(suggestedCity)}
            disabled={loading}
            className="text-xs bg-[#F5F7FA] hover:bg-[#D9E0E7]/40 text-[#123B63] font-medium px-2.5 py-1 rounded border border-[#D9E0E7] hover:border-[#cbd5e1] transition-all"
          >
            {suggestedCity}
          </button>
        ))}
      </div>
    </div>
  );
}

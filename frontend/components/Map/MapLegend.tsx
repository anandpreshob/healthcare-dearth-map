"use client";

export default function MapLegend() {
  return (
    <div className="glass-panel p-3 w-64 animate-fade-in">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-text-secondary uppercase tracking-wider">
          Dearth Score
        </span>
      </div>

      {/* Gradient bar */}
      <div className="legend-gradient h-2.5 rounded-full" />

      {/* Scale labels */}
      <div className="flex justify-between mt-1 text-[10px] text-text-muted">
        <span>0</span>
        <span>25</span>
        <span>50</span>
        <span>75</span>
        <span>100</span>
      </div>

      {/* End labels */}
      <div className="flex justify-between mt-1 text-[10px]">
        <span className="text-[#22c55e]">Well Served</span>
        <span className="text-[#ef4444]">Severe</span>
      </div>

      {/* No-data indicator */}
      <div className="flex items-center gap-2 mt-2 pt-2 border-t border-white/[0.06]">
        <span
          className="inline-block w-3 h-3 rounded-sm opacity-40"
          style={{ backgroundColor: "#1e1e32" }}
        />
        <span className="text-[10px] text-text-muted">No data</span>
      </div>
    </div>
  );
}

"use client";

import { LEGEND_ITEMS } from "@/lib/colors";

export default function MapLegend() {
  return (
    <div className="bg-white rounded-lg shadow p-3">
      <h3 className="text-sm font-semibold mb-2">Dearth Score</h3>
      <div className="space-y-1">
        {LEGEND_ITEMS.map((item) => (
          <div key={item.label} className="flex items-center gap-2 text-xs">
            <span
              className="inline-block w-4 h-4 rounded-sm flex-shrink-0"
              style={{ backgroundColor: item.color }}
            />
            <span>{item.label}</span>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-gray-400 mt-2">
        Higher score = greater healthcare shortage
      </p>
    </div>
  );
}

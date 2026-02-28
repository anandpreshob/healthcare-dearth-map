"use client";

import { useState, useCallback } from "react";
import MapView from "@/components/Map/MapView";
import MapLegend from "@/components/Map/MapLegend";
import MapControls from "@/components/Map/MapControls";
import DetailPanel from "@/components/Panels/DetailPanel";
import { useMapData } from "@/hooks/useMapData";

export default function HomePage() {
  const [specialty, setSpecialty] = useState<string | undefined>();
  const [selectedFips, setSelectedFips] = useState<string | null>(null);

  const { counties, stateBorders, nationOutline, isLoading } =
    useMapData(specialty);

  const handleCountySelect = useCallback((fips: string) => {
    setSelectedFips(fips);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedFips(null);
  }, []);

  return (
    <div className="h-[calc(100vh-2.5rem)] relative">
      {/* Map fills entire area */}
      <MapView
        counties={counties}
        stateBorders={stateBorders}
        nationOutline={nationOutline}
        onCountySelect={handleCountySelect}
        selectedFips={selectedFips}
      />

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 z-40 flex items-center justify-center bg-surface-900/60 backdrop-blur-sm">
          <div className="glass-panel px-6 py-4 flex items-center gap-3">
            <svg
              className="w-5 h-5 animate-spin text-accent"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="3"
                strokeDasharray="32"
                strokeLinecap="round"
              />
            </svg>
            <span className="text-sm text-text-secondary">
              Loading map data...
            </span>
          </div>
        </div>
      )}

      {/* Left sidebar panel — always visible */}
      <div className="absolute top-4 left-4 z-30 w-64 flex flex-col gap-3">
        {/* About section */}
        <div className="glass-panel p-3 animate-fade-in">
          <h2 className="text-sm font-semibold text-text-primary mb-1.5">
            Healthcare Dearth Map
          </h2>
          <p className="text-xs text-text-secondary leading-relaxed">
            Visualizing healthcare provider shortages across 3,109 US counties
            for 15 medical specialties. Counties are colored from{" "}
            <span className="text-[#22c55e] font-medium">green</span> (well
            served) to <span className="text-[#ef4444] font-medium">red</span>{" "}
            (severe shortage) based on provider density and road-network drive
            times.
          </p>
        </div>

        {/* Controls (specialty + search) — z-10 so search dropdown overlays panels below */}
        <div className="relative z-10">
          <MapControls
            specialty={specialty}
            onSpecialtyChange={setSpecialty}
            onCountySelect={handleCountySelect}
          />
        </div>

        {/* How to use */}
        <div className="glass-panel p-3 animate-fade-in">
          <span className="text-xs font-medium text-text-secondary uppercase tracking-wider">
            How to Use
          </span>
          <ul className="mt-2 text-xs text-text-muted space-y-1.5">
            <li className="flex gap-1.5">
              <span className="text-text-secondary shrink-0">1.</span>
              <span>
                <span className="text-text-secondary font-medium">
                  Click a state
                </span>{" "}
                to zoom in and see county-level detail
              </span>
            </li>
            <li className="flex gap-1.5">
              <span className="text-text-secondary shrink-0">2.</span>
              <span>
                <span className="text-text-secondary font-medium">
                  Click a county
                </span>{" "}
                to view scores for all 15 specialties
              </span>
            </li>
            <li className="flex gap-1.5">
              <span className="text-text-secondary shrink-0">3.</span>
              <span>
                <span className="text-text-secondary font-medium">
                  Switch specialties
                </span>{" "}
                using the dropdown above
              </span>
            </li>
            <li className="flex gap-1.5">
              <span className="text-text-secondary shrink-0">4.</span>
              <span>
                <span className="text-text-secondary font-medium">Search</span>{" "}
                for any county or zip code by name
              </span>
            </li>
          </ul>
        </div>

        {/* Legend */}
        <MapLegend />
      </div>

      {/* Floating right detail panel */}
      {selectedFips && (
        <div className="absolute top-4 right-4 z-30">
          <DetailPanel fips={selectedFips} onClose={handleCloseDetail} />
        </div>
      )}
    </div>
  );
}

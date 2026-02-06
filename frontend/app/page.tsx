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

      {/* Floating top-left controls */}
      <div className="absolute top-4 left-4 z-30">
        <MapControls
          specialty={specialty}
          onSpecialtyChange={setSpecialty}
          onCountySelect={handleCountySelect}
        />
      </div>

      {/* Floating bottom-left legend */}
      <div className="absolute bottom-6 left-4 z-30">
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

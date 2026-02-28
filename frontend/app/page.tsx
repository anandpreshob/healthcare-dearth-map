"use client";

import { useState, useCallback, useEffect } from "react";
import MapView from "@/components/Map/MapView";
import MapLegend from "@/components/Map/MapLegend";
import MapControls from "@/components/Map/MapControls";
import DetailPanel from "@/components/Panels/DetailPanel";
import { useMapData } from "@/hooks/useMapData";

function InfoBanner({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 glass-panel px-5 py-4 max-w-md animate-fade-in">
      <div className="flex items-start gap-3">
        <div className="flex-1 space-y-2">
          <h2 className="text-sm font-semibold text-text-primary">
            Healthcare Dearth Map
          </h2>
          <p className="text-xs text-text-secondary leading-relaxed">
            This map visualizes healthcare provider shortages across all 3,109 US
            counties for 15 medical specialties. Counties are colored from{" "}
            <span className="text-[#22c55e] font-medium">green</span> (well
            served) to <span className="text-[#ef4444] font-medium">red</span>{" "}
            (severe shortage) based on provider density and road-network drive
            times.
          </p>
          <ul className="text-xs text-text-muted space-y-1">
            <li>
              <span className="text-text-secondary font-medium">Click a state</span>{" "}
              to zoom in and see county-level detail
            </li>
            <li>
              <span className="text-text-secondary font-medium">Click a county</span>{" "}
              (when zoomed in) to view scores for all 15 specialties
            </li>
            <li>
              <span className="text-text-secondary font-medium">
                Switch specialties
              </span>{" "}
              using the dropdown on the left
            </li>
            <li>
              <span className="text-text-secondary font-medium">Search</span>{" "}
              for any county or zip code by name
            </li>
          </ul>
        </div>
        <button
          onClick={onDismiss}
          className="text-text-muted hover:text-text-primary transition-colors mt-0.5 shrink-0"
          aria-label="Dismiss"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default function HomePage() {
  const [specialty, setSpecialty] = useState<string | undefined>();
  const [selectedFips, setSelectedFips] = useState<string | null>(null);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    // Show info banner on first visit
    const dismissed = sessionStorage.getItem("info-dismissed");
    if (!dismissed) {
      setShowInfo(true);
    }
  }, []);

  const handleDismissInfo = useCallback(() => {
    setShowInfo(false);
    sessionStorage.setItem("info-dismissed", "1");
  }, []);

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

      {/* Info banner (shown on first visit) */}
      {showInfo && !isLoading && (
        <InfoBanner onDismiss={handleDismissInfo} />
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

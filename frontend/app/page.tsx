"use client";

import { useState, useCallback } from "react";
import MapView from "@/components/Map/MapView";
import MapLegend from "@/components/Map/MapLegend";
import SpecialtySelector from "@/components/Panels/SpecialtySelector";
import SearchBar from "@/components/Panels/SearchBar";
import DetailPanel from "@/components/Panels/DetailPanel";
import { useGeoJSON } from "@/hooks/useGeoJSON";

export default function HomePage() {
  const [specialty, setSpecialty] = useState<string | undefined>();
  const [selectedFips, setSelectedFips] = useState<string | null>(null);

  const { data: geojsonData, isLoading } = useGeoJSON(specialty);

  const handleCountySelect = useCallback((fips: string) => {
    setSelectedFips(fips);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedFips(null);
  }, []);

  return (
    <div className="h-[calc(100vh-3.5rem)] flex">
      {/* Sidebar controls */}
      <div className="w-80 flex-shrink-0 bg-white border-r p-4 space-y-4 overflow-y-auto">
        <SpecialtySelector value={specialty} onChange={setSpecialty} />
        <SearchBar onSelect={handleCountySelect} />
        <MapLegend />

        {selectedFips && (
          <DetailPanel fips={selectedFips} onClose={handleCloseDetail} />
        )}
      </div>

      {/* Map area */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/60">
            <p className="text-gray-500">Loading map data...</p>
          </div>
        )}
        <MapView
          geojsonData={geojsonData}
          onCountySelect={handleCountySelect}
          selectedFips={selectedFips}
        />
      </div>
    </div>
  );
}

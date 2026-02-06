"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import maplibregl from "maplibre-gl";
import {
  BASEMAP_STYLE,
  US_CENTER,
  DEFAULT_ZOOM,
  COUNTIES_SOURCE,
  COUNTIES_FILL_LAYER,
  COUNTIES_LINE_LAYER,
} from "@/lib/constants";
import { SCORE_COLOR_STOPS } from "@/lib/colors";
import type { GeoJSONFeatureCollection } from "@/types";

interface MapViewProps {
  geojsonData?: GeoJSONFeatureCollection;
  onCountySelect: (fips: string) => void;
  selectedFips?: string | null;
}

export default function MapView({
  geojsonData,
  onCountySelect,
  selectedFips,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP_STYLE,
      center: US_CENTER,
      zoom: DEFAULT_ZOOM,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    popupRef.current = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
    });

    map.on("load", () => {
      setMapLoaded(true);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update GeoJSON data on the map
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded || !geojsonData) return;

    const source = map.getSource(COUNTIES_SOURCE) as
      | maplibregl.GeoJSONSource
      | undefined;

    if (source) {
      source.setData(geojsonData as unknown as GeoJSON.FeatureCollection);
    } else {
      map.addSource(COUNTIES_SOURCE, {
        type: "geojson",
        data: geojsonData as unknown as GeoJSON.FeatureCollection,
      });

      // Build the color interpolation stops
      const colorStops = SCORE_COLOR_STOPS.flatMap(([score, color]) => [
        score,
        color,
      ]);

      map.addLayer({
        id: COUNTIES_FILL_LAYER,
        type: "fill",
        source: COUNTIES_SOURCE,
        paint: {
          "fill-color": [
            "interpolate",
            ["linear"],
            ["get", "dearth_score"],
            ...colorStops,
          ],
          "fill-opacity": [
            "case",
            ["boolean", ["feature-state", "hover"], false],
            0.85,
            0.7,
          ],
        },
      });

      map.addLayer({
        id: COUNTIES_LINE_LAYER,
        type: "line",
        source: COUNTIES_SOURCE,
        paint: {
          "line-color": "#666",
          "line-width": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            2.5,
            0.5,
          ],
        },
      });

      // Hover handler
      let hoveredId: string | number | null = null;

      map.on("mousemove", COUNTIES_FILL_LAYER, (e) => {
        if (!e.features || e.features.length === 0) return;

        map.getCanvas().style.cursor = "pointer";

        if (hoveredId !== null) {
          map.setFeatureState(
            { source: COUNTIES_SOURCE, id: hoveredId },
            { hover: false }
          );
        }

        hoveredId = e.features[0].id ?? null;
        if (hoveredId !== null) {
          map.setFeatureState(
            { source: COUNTIES_SOURCE, id: hoveredId },
            { hover: true }
          );
        }

        const props = e.features[0].properties;
        const score = props?.dearth_score ?? "N/A";
        const name = props?.name ?? "Unknown";
        const state = props?.state ?? "";

        popupRef.current
          ?.setLngLat(e.lngLat)
          .setHTML(
            `<div class="text-sm"><strong>${name}, ${state}</strong><br/>Dearth Score: <strong>${Math.round(score)}</strong></div>`
          )
          .addTo(map);
      });

      map.on("mouseleave", COUNTIES_FILL_LAYER, () => {
        map.getCanvas().style.cursor = "";
        if (hoveredId !== null) {
          map.setFeatureState(
            { source: COUNTIES_SOURCE, id: hoveredId },
            { hover: false }
          );
        }
        hoveredId = null;
        popupRef.current?.remove();
      });

      // Click handler
      map.on("click", COUNTIES_FILL_LAYER, (e) => {
        if (!e.features || e.features.length === 0) return;
        const fips = e.features[0].properties?.fips;
        if (fips) onCountySelect(fips);
      });
    }
  }, [geojsonData, mapLoaded, onCountySelect]);

  // Highlight selected county
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded || !geojsonData) return;

    // Clear all selected states first
    geojsonData.features.forEach((_, idx) => {
      map.setFeatureState(
        { source: COUNTIES_SOURCE, id: idx },
        { selected: false }
      );
    });

    if (selectedFips) {
      const idx = geojsonData.features.findIndex(
        (f) => f.properties.fips === selectedFips
      );
      if (idx >= 0) {
        map.setFeatureState(
          { source: COUNTIES_SOURCE, id: idx },
          { selected: true }
        );
      }
    }
  }, [selectedFips, geojsonData, mapLoaded]);

  return (
    <div ref={containerRef} className="w-full h-full min-h-[500px] rounded-lg" />
  );
}

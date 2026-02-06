"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import maplibregl from "maplibre-gl";
import {
  BLANK_STYLE,
  US_CENTER,
  DEFAULT_ZOOM,
  US_BOUNDS,
  MIN_ZOOM,
  MAX_ZOOM,
  STATE_ZOOM_THRESHOLD,
  COUNTIES_SOURCE,
  COUNTIES_FILL_LAYER,
  COUNTIES_LINE_LAYER,
  STATES_SOURCE,
  STATES_LINE_LAYER,
  NATION_SOURCE,
  NATION_LINE_LAYER,
} from "@/lib/constants";
import { SCORE_COLOR_STOPS, NO_DATA_COLOR } from "@/lib/colors";
import type {
  FeatureCollection,
  Polygon,
  MultiPolygon,
  MultiLineString,
} from "geojson";

interface MapViewProps {
  counties: FeatureCollection<Polygon | MultiPolygon>;
  stateBorders: MultiLineString;
  nationOutline: MultiLineString;
  onCountySelect: (fips: string) => void;
  selectedFips?: string | null;
}

export default function MapView({
  counties,
  stateBorders,
  nationOutline,
  onCountySelect,
  selectedFips,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [currentZoom, setCurrentZoom] = useState(DEFAULT_ZOOM);

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BLANK_STYLE,
      center: US_CENTER,
      zoom: DEFAULT_ZOOM,
      maxBounds: US_BOUNDS,
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    popupRef.current = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      maxWidth: "280px",
    });

    map.on("zoomend", () => {
      setCurrentZoom(map.getZoom());
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

  // Add/update sources and layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    // -- Counties source --
    const countySource = map.getSource(COUNTIES_SOURCE) as
      | maplibregl.GeoJSONSource
      | undefined;

    if (countySource) {
      countySource.setData(counties);
    } else {
      map.addSource(COUNTIES_SOURCE, {
        type: "geojson",
        data: counties,
        promoteId: "fips",
      });

      const colorStops = SCORE_COLOR_STOPS.flatMap(([score, color]) => [
        score,
        color,
      ]);

      // Counties fill layer
      map.addLayer({
        id: COUNTIES_FILL_LAYER,
        type: "fill",
        source: COUNTIES_SOURCE,
        paint: {
          "fill-color": [
            "case",
            ["==", ["get", "hasData"], false],
            NO_DATA_COLOR,
            ["!", ["has", "dearth_score"]],
            NO_DATA_COLOR,
            ["interpolate", ["linear"], ["get", "dearth_score"], ...colorStops],
          ],
          "fill-opacity": [
            "case",
            ["==", ["get", "hasData"], false],
            0.3,
            [
              "case",
              ["boolean", ["feature-state", "hover"], false],
              0.9,
              0.75,
            ],
          ],
        },
      });

      // Counties line layer
      map.addLayer({
        id: COUNTIES_LINE_LAYER,
        type: "line",
        source: COUNTIES_SOURCE,
        paint: {
          "line-color": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            "#60a5fa",
            "rgba(255, 255, 255, 0.08)",
          ],
          "line-width": [
            "interpolate",
            ["linear"],
            ["zoom"],
            3, 0.1,
            10, 0.8,
          ],
        },
      });

      // -- State borders --
      map.addSource(STATES_SOURCE, {
        type: "geojson",
        data: { type: "Feature", geometry: stateBorders, properties: {} },
      });

      map.addLayer({
        id: STATES_LINE_LAYER,
        type: "line",
        source: STATES_SOURCE,
        paint: {
          "line-color": "rgba(255, 255, 255, 0.2)",
          "line-width": [
            "interpolate",
            ["linear"],
            ["zoom"],
            3,
            0.8,
            10,
            2,
          ],
        },
      });

      // -- Nation outline --
      map.addSource(NATION_SOURCE, {
        type: "geojson",
        data: { type: "Feature", geometry: nationOutline, properties: {} },
      });

      map.addLayer({
        id: NATION_LINE_LAYER,
        type: "line",
        source: NATION_SOURCE,
        paint: {
          "line-color": "rgba(255, 255, 255, 0.35)",
          "line-width": [
            "interpolate",
            ["linear"],
            ["zoom"],
            3,
            1,
            10,
            2.5,
          ],
        },
      });

      // -- Hover interactions --
      let hoveredFips: string | null = null;

      map.on("mousemove", COUNTIES_FILL_LAYER, (e) => {
        if (!e.features || e.features.length === 0) return;

        map.getCanvas().style.cursor = "pointer";
        const props = e.features[0].properties;
        const fips = props?.fips;

        if (hoveredFips && hoveredFips !== fips) {
          map.setFeatureState(
            { source: COUNTIES_SOURCE, id: hoveredFips },
            { hover: false }
          );
        }

        if (fips) {
          hoveredFips = fips;
          map.setFeatureState(
            { source: COUNTIES_SOURCE, id: fips },
            { hover: true }
          );
        }

        const hasData = props?.hasData;
        const score = props?.dearth_score;
        const name = props?.name ?? "Unknown";
        const state = props?.state ?? "";
        const providerCount = props?.provider_count;

        let scoreHtml: string;
        if (hasData && score != null) {
          const scoreColor =
            score <= 20
              ? "#22c55e"
              : score <= 40
              ? "#84cc16"
              : score <= 60
              ? "#f59e0b"
              : score <= 80
              ? "#f97316"
              : "#ef4444";
          scoreHtml = `
            <div style="display:flex;align-items:center;gap:6px;margin-top:4px;">
              <span style="width:8px;height:8px;border-radius:50%;background:${scoreColor};display:inline-block;"></span>
              <span style="font-weight:600;">${Math.round(score)}</span>
              <span style="color:#94a3c4;font-size:11px;">/ 100</span>
            </div>`;
          if (providerCount != null) {
            scoreHtml += `<div style="color:#94a3c4;font-size:11px;margin-top:2px;">${providerCount} providers</div>`;
          }
        } else {
          scoreHtml = `<div style="color:#5b6b8a;margin-top:4px;font-size:11px;">No data available</div>`;
        }

        const displayName = hasData ? `${name}, ${state}` : `FIPS ${fips}`;

        popupRef.current
          ?.setLngLat(e.lngLat)
          .setHTML(
            `<div><strong style="font-size:13px;">${displayName}</strong>${scoreHtml}</div>`
          )
          .addTo(map);
      });

      map.on("mouseleave", COUNTIES_FILL_LAYER, () => {
        map.getCanvas().style.cursor = "";
        if (hoveredFips) {
          map.setFeatureState(
            { source: COUNTIES_SOURCE, id: hoveredFips },
            { hover: false }
          );
          hoveredFips = null;
        }
        popupRef.current?.remove();
      });

      // -- Click handler with drill-down --
      map.on("click", COUNTIES_FILL_LAYER, (e) => {
        if (!e.features || e.features.length === 0) return;
        const props = e.features[0].properties;
        const fips = props?.fips as string;
        if (!fips) return;

        const zoom = map.getZoom();
        if (zoom < STATE_ZOOM_THRESHOLD) {
          // Drill-down: zoom to the state containing this county
          const stateFips = fips.slice(0, 2);
          const stateCounties = counties.features.filter(
            (f) =>
              ((f.properties as Record<string, unknown>)?.fips as string)?.startsWith(stateFips)
          );
          if (stateCounties.length > 0) {
            const bounds = new maplibregl.LngLatBounds();
            for (const c of stateCounties) {
              const coords = c.geometry.type === "Polygon"
                ? c.geometry.coordinates
                : c.geometry.coordinates.flat();
              for (const ring of coords) {
                for (const pt of ring as number[][]) {
                  bounds.extend(pt as [number, number]);
                }
              }
            }
            map.fitBounds(bounds, { padding: 50, duration: 1200 });
          }
        } else {
          // County-level: select county
          if (props?.hasData) {
            onCountySelect(fips);
          }
        }
      });
    }
  }, [counties, stateBorders, nationOutline, mapLoaded, onCountySelect]);

  // Highlight selected county
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    // Clear previous selection - we track by feature-state on the source
    // Just set selected on the new fips
    if (selectedFips) {
      map.setFeatureState(
        { source: COUNTIES_SOURCE, id: selectedFips },
        { selected: true }
      );
    }

    return () => {
      if (selectedFips && mapRef.current) {
        try {
          mapRef.current.setFeatureState(
            { source: COUNTIES_SOURCE, id: selectedFips },
            { selected: false }
          );
        } catch {
          // Map may have been removed
        }
      }
    };
  }, [selectedFips, mapLoaded]);

  // Fly to selected county
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded || !selectedFips) return;

    const feature = counties.features.find(
      (f) => (f.properties as Record<string, unknown>)?.fips === selectedFips
    );
    if (!feature) return;

    const bounds = new maplibregl.LngLatBounds();
    const coords =
      feature.geometry.type === "Polygon"
        ? feature.geometry.coordinates
        : feature.geometry.coordinates.flat();
    for (const ring of coords) {
      for (const pt of ring as number[][]) {
        bounds.extend(pt as [number, number]);
      }
    }

    map.fitBounds(bounds, {
      padding: 100,
      maxZoom: 9,
      duration: 1000,
    });
  }, [selectedFips, counties, mapLoaded]);

  const handleResetView = useCallback(() => {
    mapRef.current?.flyTo({
      center: US_CENTER,
      zoom: DEFAULT_ZOOM,
      duration: 1200,
    });
  }, []);

  return (
    <>
      <div
        ref={containerRef}
        className="w-full h-full"
      />
      {currentZoom > STATE_ZOOM_THRESHOLD && (
        <button
          onClick={handleResetView}
          className="absolute top-4 left-1/2 -translate-x-1/2 z-30 glass-panel px-4 py-1.5 text-xs font-medium text-text-secondary hover:text-text-primary transition-colors animate-fade-in"
        >
          Back to US
        </button>
      )}
    </>
  );
}

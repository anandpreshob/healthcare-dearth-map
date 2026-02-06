/** Geographic center of the contiguous US */
export const US_CENTER: [number, number] = [-98.5, 39.8];

/** Default zoom level for the US map */
export const DEFAULT_ZOOM = 4;

/** Blank dark style - no basemap tiles, just a dark background */
export const BLANK_STYLE: maplibregl.StyleSpecification = {
  version: 8 as const,
  sources: {},
  layers: [
    {
      id: "background",
      type: "background" as const,
      paint: { "background-color": "#0f0f1a" },
    },
  ],
};

/** Bounds constraining map to continental US */
export const US_BOUNDS: [[number, number], [number, number]] = [
  [-135, 20],
  [-60, 53],
];

/** Zoom threshold: below = state drill-down click, above = county select */
export const STATE_ZOOM_THRESHOLD = 6;

/** Min/max zoom */
export const MIN_ZOOM = 3;
export const MAX_ZOOM = 12;

/** Map source and layer IDs */
export const COUNTIES_SOURCE = "counties";
export const COUNTIES_FILL_LAYER = "counties-fill";
export const COUNTIES_LINE_LAYER = "counties-line";
export const STATES_SOURCE = "states-borders";
export const STATES_LINE_LAYER = "states-line";
export const NATION_SOURCE = "nation-outline";
export const NATION_LINE_LAYER = "nation-line";

import type maplibregl from "maplibre-gl";

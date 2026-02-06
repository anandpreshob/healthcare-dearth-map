/** No-data fill color (dark gray that blends with background) */
export const NO_DATA_COLOR = "#1e1e32";

/** Map background color */
export const MAP_BG_COLOR = "#0f0f1a";

/**
 * Returns a hex color for a dearth score (0-100).
 * Lower score = better access (green), higher = worse (red).
 * Brighter colors for dark background contrast.
 */
export function getColorForScore(score: number): string {
  if (score <= 20) return "#22c55e";
  if (score <= 40) return "#84cc16";
  if (score <= 60) return "#f59e0b";
  if (score <= 80) return "#f97316";
  return "#ef4444";
}

export function getLabelForScore(score: number): string {
  if (score <= 20) return "Well Served";
  if (score <= 40) return "Adequate";
  if (score <= 60) return "Moderate Shortage";
  if (score <= 80) return "Significant Shortage";
  return "Severe Shortage";
}

/** Color stops for MapLibre interpolation */
export const SCORE_COLOR_STOPS: [number, string][] = [
  [0, "#22c55e"],
  [20, "#22c55e"],
  [21, "#84cc16"],
  [40, "#84cc16"],
  [41, "#f59e0b"],
  [60, "#f59e0b"],
  [61, "#f97316"],
  [80, "#f97316"],
  [81, "#ef4444"],
  [100, "#ef4444"],
];

/** Legend items for display */
export const LEGEND_ITEMS = [
  { min: 0, max: 20, color: "#22c55e", label: "Well Served" },
  { min: 21, max: 40, color: "#84cc16", label: "Adequate" },
  { min: 41, max: 60, color: "#f59e0b", label: "Moderate Shortage" },
  { min: 61, max: 80, color: "#f97316", label: "Significant Shortage" },
  { min: 81, max: 100, color: "#ef4444", label: "Severe Shortage" },
];

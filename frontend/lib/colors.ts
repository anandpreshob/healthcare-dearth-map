/**
 * Returns a hex color for a dearth score (0-100).
 * Lower score = better access (green), higher = worse (red).
 */
export function getColorForScore(score: number): string {
  if (score <= 20) return "#1a9850";
  if (score <= 40) return "#91cf60";
  if (score <= 60) return "#fee08b";
  if (score <= 80) return "#fc8d59";
  return "#d73027";
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
  [0, "#1a9850"],
  [20, "#1a9850"],
  [21, "#91cf60"],
  [40, "#91cf60"],
  [41, "#fee08b"],
  [60, "#fee08b"],
  [61, "#fc8d59"],
  [80, "#fc8d59"],
  [81, "#d73027"],
  [100, "#d73027"],
];

/** Legend items for display */
export const LEGEND_ITEMS = [
  { min: 0, max: 20, color: "#1a9850", label: "Well Served (0-20)" },
  { min: 21, max: 40, color: "#91cf60", label: "Adequate (21-40)" },
  { min: 41, max: 60, color: "#fee08b", label: "Moderate Shortage (41-60)" },
  { min: 61, max: 80, color: "#fc8d59", label: "Significant Shortage (61-80)" },
  { min: 81, max: 100, color: "#d73027", label: "Severe Shortage (81-100)" },
];

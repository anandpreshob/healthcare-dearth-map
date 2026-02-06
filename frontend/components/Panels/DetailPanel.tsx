"use client";

import { useCountyDetail } from "@/hooks/useCountyDetail";
import { getColorForScore } from "@/lib/colors";

interface DetailPanelProps {
  fips: string | null;
  onClose: () => void;
}

export default function DetailPanel({ fips, onClose }: DetailPanelProps) {
  const { data: county, isLoading, error } = useCountyDetail(fips);

  if (!fips) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 w-full max-w-sm overflow-y-auto max-h-[calc(100vh-12rem)]">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">County Detail</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          aria-label="Close detail panel"
        >
          &times;
        </button>
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading...</p>}
      {error && (
        <p className="text-sm text-red-500">Failed to load county data.</p>
      )}

      {county && (
        <div className="space-y-3">
          <div>
            <h3 className="font-semibold text-base">
              {county.name}, {county.state}
            </h3>
            <p className="text-xs text-gray-500">FIPS: {county.fips}</p>
          </div>

          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="bg-gray-50 rounded p-2">
              <div className="text-gray-500 text-xs">Population</div>
              <div className="font-medium">
                {county.population?.toLocaleString() ?? "N/A"}
              </div>
            </div>
          </div>

          {county.specialties.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-1">
                Scores by Specialty
              </h4>
              <div className="border rounded overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left p-1.5">Specialty</th>
                      <th className="text-right p-1.5">Providers</th>
                      <th className="text-right p-1.5">Score</th>
                      <th className="text-right p-1.5">vs State</th>
                    </tr>
                  </thead>
                  <tbody>
                    {county.specialties.map((ss) => (
                      <tr key={ss.code} className="border-t">
                        <td className="p-1.5">{ss.name}</td>
                        <td className="text-right p-1.5">
                          {ss.provider_count ?? 0}
                        </td>
                        <td className="text-right p-1.5">
                          {ss.dearth_score != null ? (
                            <span className="inline-flex items-center gap-1">
                              <span
                                className="inline-block w-2 h-2 rounded-full"
                                style={{
                                  backgroundColor: getColorForScore(
                                    ss.dearth_score
                                  ),
                                }}
                              />
                              {Math.round(ss.dearth_score)}
                            </span>
                          ) : (
                            "N/A"
                          )}
                        </td>
                        <td className="text-right p-1.5 text-gray-500">
                          {ss.dearth_score != null && ss.state_avg_score != null
                            ? `${(ss.dearth_score - ss.state_avg_score) >= 0 ? "+" : ""}${(
                                ss.dearth_score - ss.state_avg_score
                              ).toFixed(1)}`
                            : ""}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

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

  // Compute overall score from first specialty or average
  const overallScore =
    county?.specialties?.[0]?.dearth_score ?? null;

  return (
    <div className="glass-panel w-[360px] max-h-[calc(100vh-6rem)] flex flex-col animate-slide-in-right">
      {/* Header */}
      <div className="flex items-center justify-between p-4 pb-3 border-b border-white/[0.06]">
        <h2 className="text-sm font-semibold text-text-primary">
          County Detail
        </h2>
        <button
          onClick={onClose}
          className="text-text-muted hover:text-text-primary text-lg leading-none w-6 h-6 flex items-center justify-center rounded hover:bg-white/[0.05] transition-colors"
          aria-label="Close detail panel"
        >
          &times;
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading && (
          <div className="flex items-center gap-2 text-text-muted text-sm py-8 justify-center">
            <svg
              className="w-4 h-4 animate-spin"
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
            Loading...
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm text-red-400">
            Failed to load county data.
          </div>
        )}

        {county && (
          <>
            {/* County info */}
            <div>
              <h3 className="font-semibold text-base text-text-primary">
                {county.name}, {county.state}
              </h3>
              <p className="text-[11px] text-text-muted mt-0.5">
                FIPS: {county.fips}
              </p>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-surface-700/80 rounded-lg p-3">
                <div className="text-[10px] text-text-muted uppercase tracking-wider">
                  Population
                </div>
                <div className="text-lg font-semibold text-text-primary mt-0.5">
                  {county.population?.toLocaleString() ?? "N/A"}
                </div>
              </div>
              <div className="bg-surface-700/80 rounded-lg p-3">
                <div className="text-[10px] text-text-muted uppercase tracking-wider">
                  Overall Score
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  {overallScore != null ? (
                    <>
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor: getColorForScore(overallScore),
                        }}
                      />
                      <span className="text-lg font-semibold text-text-primary">
                        {Math.round(overallScore)}
                      </span>
                    </>
                  ) : (
                    <span className="text-lg font-semibold text-text-muted">
                      N/A
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Specialty scores table */}
            {county.specialties.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wider">
                  Scores by Specialty
                </h4>
                <div className="border border-white/[0.06] rounded-lg overflow-hidden">
                  <table className="w-full text-xs">
                    <thead className="bg-surface-700/80">
                      <tr>
                        <th className="text-left p-2 text-text-muted font-medium">
                          Specialty
                        </th>
                        <th className="text-right p-2 text-text-muted font-medium">
                          Providers
                        </th>
                        <th className="text-right p-2 text-text-muted font-medium">
                          Score
                        </th>
                        <th className="text-right p-2 text-text-muted font-medium">
                          vs State
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {county.specialties.map((ss) => {
                        const diff =
                          ss.dearth_score != null && ss.state_avg_score != null
                            ? ss.dearth_score - ss.state_avg_score
                            : null;
                        return (
                          <tr
                            key={ss.code}
                            className="border-t border-white/[0.06] hover:bg-white/[0.03]"
                          >
                            <td className="p-2 text-text-primary">
                              {ss.name}
                            </td>
                            <td className="text-right p-2 font-mono text-text-secondary">
                              {ss.provider_count ?? 0}
                            </td>
                            <td className="text-right p-2">
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
                                  <span className="font-mono text-text-primary">
                                    {Math.round(ss.dearth_score)}
                                  </span>
                                </span>
                              ) : (
                                <span className="text-text-muted">N/A</span>
                              )}
                            </td>
                            <td className="text-right p-2 font-mono">
                              {diff != null ? (
                                <span
                                  className={
                                    diff > 0
                                      ? "text-red-400"
                                      : diff < 0
                                      ? "text-green-400"
                                      : "text-text-muted"
                                  }
                                >
                                  {diff >= 0 ? "+" : ""}
                                  {diff.toFixed(1)}
                                </span>
                              ) : (
                                ""
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

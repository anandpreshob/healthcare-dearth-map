"use client";

import { useState, useMemo } from "react";
import type { CountySummary } from "@/types";
import { getColorForScore } from "@/lib/colors";

type SortField =
  | "name"
  | "state"
  | "population"
  | "dearth_score"
  | "dearth_label"
  | "provider_count"
  | "provider_density";
type SortDir = "asc" | "desc";

interface DataTableProps {
  data: CountySummary[];
  isLoading: boolean;
}

const COLUMNS: { key: SortField; label: string; align?: "right" }[] = [
  { key: "name", label: "County" },
  { key: "state", label: "State" },
  { key: "population", label: "Population", align: "right" },
  { key: "dearth_score", label: "Score", align: "right" },
  { key: "dearth_label", label: "Label" },
  { key: "provider_count", label: "Providers", align: "right" },
  { key: "provider_density", label: "Density", align: "right" },
];

export default function DataTable({ data, isLoading }: DataTableProps) {
  const [sortField, setSortField] = useState<SortField>("dearth_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const sorted = useMemo(() => {
    if (!data) return [];
    return [...data].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDir === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      const aNum = Number(aVal);
      const bNum = Number(bVal);
      return sortDir === "asc" ? aNum - bNum : bNum - aNum;
    });
  }, [data, sortField, sortDir]);

  function handleSort(field: SortField) {
    if (field === sortField) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  }

  if (isLoading) {
    return (
      <div className="text-center py-10 text-text-muted">Loading data...</div>
    );
  }

  return (
    <div className="overflow-x-auto border border-white/[0.06] rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-surface-700/80 border-b border-white/[0.06]">
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                className={`px-3 py-2 font-medium text-text-muted cursor-pointer select-none hover:bg-white/[0.03] ${
                  col.align === "right" ? "text-right" : "text-left"
                }`}
                onClick={() => handleSort(col.key)}
              >
                {col.label}
                {sortField === col.key && (
                  <span className="ml-1">
                    {sortDir === "asc" ? "\u2191" : "\u2193"}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr
              key={row.fips}
              className="border-t border-white/[0.06] hover:bg-white/[0.03]"
            >
              <td className="px-3 py-2 text-text-primary">{row.name}</td>
              <td className="px-3 py-2 text-text-secondary">{row.state}</td>
              <td className="px-3 py-2 text-right text-text-secondary font-mono">
                {row.population?.toLocaleString() ?? "N/A"}
              </td>
              <td className="px-3 py-2 text-right">
                {row.dearth_score != null ? (
                  <>
                    <span
                      className="inline-block w-2.5 h-2.5 rounded-full mr-1.5"
                      style={{
                        backgroundColor: getColorForScore(row.dearth_score),
                      }}
                    />
                    <span className="font-mono text-text-primary">
                      {Math.round(row.dearth_score)}
                    </span>
                  </>
                ) : (
                  <span className="text-text-muted">N/A</span>
                )}
              </td>
              <td className="px-3 py-2 text-text-secondary">
                {row.dearth_label ?? "N/A"}
              </td>
              <td className="px-3 py-2 text-right font-mono text-text-secondary">
                {row.provider_count ?? 0}
              </td>
              <td className="px-3 py-2 text-right font-mono text-text-secondary">
                {row.provider_density != null
                  ? row.provider_density.toFixed(2)
                  : "N/A"}
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td
                colSpan={COLUMNS.length}
                className="px-3 py-6 text-center text-text-muted"
              >
                No data available
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

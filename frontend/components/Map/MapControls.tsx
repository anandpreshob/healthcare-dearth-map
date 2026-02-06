"use client";

import { useState, useRef } from "react";
import { useSpecialties } from "@/hooks/useSpecialties";
import { useSearch } from "@/hooks/useSearch";

interface MapControlsProps {
  specialty?: string;
  onSpecialtyChange: (specialty: string | undefined) => void;
  onCountySelect: (fips: string) => void;
}

export default function MapControls({
  specialty,
  onSpecialtyChange,
  onCountySelect,
}: MapControlsProps) {
  const { data: specialties, isLoading: specialtiesLoading } = useSpecialties();
  const { query, setQuery, results } = useSearch();
  const [searchOpen, setSearchOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="glass-panel p-3 w-72 space-y-3 animate-fade-in">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-text-secondary uppercase tracking-wider">
          Filters
        </span>
      </div>

      {/* Specialty selector */}
      <div>
        <select
          className="w-full rounded-lg border border-white/[0.08] bg-surface-700 px-3 py-1.5 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent appearance-none cursor-pointer"
          value={specialty ?? ""}
          onChange={(e) => {
            const v = e.target.value;
            onSpecialtyChange(v || undefined);
          }}
          disabled={specialtiesLoading}
        >
          <option value="">Primary Care (default)</option>
          {specialties?.map((s) => (
            <option key={s.code} value={s.code}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {/* Search input */}
      <div className="relative">
        <div className="relative">
          <svg
            className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            ref={inputRef}
            type="text"
            placeholder="Search counties or zip codes..."
            className="w-full rounded-lg border border-white/[0.08] bg-surface-700 pl-8 pr-3 py-1.5 text-sm text-text-primary placeholder-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSearchOpen(true);
            }}
            onFocus={() => setSearchOpen(true)}
            onBlur={() => setTimeout(() => setSearchOpen(false), 200)}
          />
        </div>

        {searchOpen && results.data && results.data.length > 0 && (
          <ul className="absolute z-50 mt-1 w-full bg-surface-700 border border-white/[0.08] rounded-lg shadow-glass-lg max-h-48 overflow-y-auto">
            {results.data.map((r) => (
              <li key={`${r.type}-${r.id}`}>
                <button
                  className="w-full text-left px-3 py-2 text-sm text-text-primary hover:bg-white/[0.05] flex items-center justify-between"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    onCountySelect(r.id);
                    setQuery("");
                    setSearchOpen(false);
                  }}
                >
                  <span>{r.label}</span>
                  <span className="text-[10px] text-text-muted uppercase">
                    {r.type}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}

        {searchOpen && query.length >= 2 && results.isLoading && (
          <div className="absolute z-50 mt-1 w-full bg-surface-700 border border-white/[0.08] rounded-lg shadow-glass-lg px-3 py-2 text-sm text-text-muted">
            Searching...
          </div>
        )}

        {searchOpen &&
          query.length >= 2 &&
          !results.isLoading &&
          results.data?.length === 0 && (
            <div className="absolute z-50 mt-1 w-full bg-surface-700 border border-white/[0.08] rounded-lg shadow-glass-lg px-3 py-2 text-sm text-text-muted">
              No results found
            </div>
          )}
      </div>
    </div>
  );
}

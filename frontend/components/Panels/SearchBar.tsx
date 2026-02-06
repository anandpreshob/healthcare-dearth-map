"use client";

import { useSearch } from "@/hooks/useSearch";
import { useRef, useState } from "react";

interface SearchBarProps {
  onSelect: (fips: string) => void;
}

export default function SearchBar({ onSelect }: SearchBarProps) {
  const { query, setQuery, results } = useSearch();
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="relative">
      <label htmlFor="search-input" className="sr-only">
        Search counties or zip codes
      </label>
      <input
        ref={inputRef}
        id="search-input"
        type="text"
        placeholder="Search counties or zip codes..."
        className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          setTimeout(() => setOpen(false), 200);
        }}
      />

      {open && results.data && results.data.length > 0 && (
        <ul className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
          {results.data.map((r) => (
            <li key={`${r.type}-${r.id}`}>
              <button
                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 flex items-center justify-between"
                onMouseDown={(e) => {
                  e.preventDefault();
                  onSelect(r.id);
                  setQuery("");
                  setOpen(false);
                }}
              >
                <span>{r.label}</span>
                <span className="text-xs text-gray-400">{r.type}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {open && query.length >= 2 && results.isLoading && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg px-3 py-2 text-sm text-gray-500">
          Searching...
        </div>
      )}

      {open &&
        query.length >= 2 &&
        !results.isLoading &&
        results.data?.length === 0 && (
          <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg px-3 py-2 text-sm text-gray-500">
            No results found
          </div>
        )}
    </div>
  );
}

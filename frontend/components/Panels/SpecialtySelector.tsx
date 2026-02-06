"use client";

import { useSpecialties } from "@/hooks/useSpecialties";

interface SpecialtySelectorProps {
  value?: string;
  onChange: (specialty: string | undefined) => void;
}

export default function SpecialtySelector({
  value,
  onChange,
}: SpecialtySelectorProps) {
  const { data: specialties, isLoading } = useSpecialties();

  return (
    <div>
      <label
        htmlFor="specialty-select"
        className="block text-sm font-medium text-gray-700 mb-1"
      >
        Specialty
      </label>
      <select
        id="specialty-select"
        className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        value={value ?? ""}
        onChange={(e) => {
          const v = e.target.value;
          onChange(v || undefined);
        }}
        disabled={isLoading}
      >
        <option value="">Primary Care (default)</option>
        {specialties?.map((s) => (
          <option key={s.code} value={s.code}>
            {s.name}
          </option>
        ))}
      </select>
    </div>
  );
}

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
        className="block text-sm font-medium text-text-secondary mb-1"
      >
        Specialty
      </label>
      <select
        id="specialty-select"
        className="w-full rounded-lg border border-white/[0.08] bg-surface-700 px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent appearance-none cursor-pointer"
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

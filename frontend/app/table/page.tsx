"use client";

import { useState } from "react";
import SpecialtySelector from "@/components/Panels/SpecialtySelector";
import DataTable from "@/components/Table/DataTable";
import ExportButton from "@/components/Table/ExportButton";
import { useCountyData } from "@/hooks/useCountyData";

export default function TablePage() {
  const [specialty, setSpecialty] = useState<string | undefined>();
  const { data, isLoading } = useCountyData(specialty);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div className="w-64">
          <SpecialtySelector value={specialty} onChange={setSpecialty} />
        </div>
        <ExportButton specialty={specialty} />
      </div>

      <DataTable data={data ?? []} isLoading={isLoading} />

      {data && (
        <p className="text-xs text-text-muted">
          Showing {data.length} counties
        </p>
      )}
    </div>
  );
}

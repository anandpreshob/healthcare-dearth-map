export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <h1 className="text-3xl font-bold text-text-primary">
        About the Healthcare Dearth Map
      </h1>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          What is a Dearth Score?
        </h2>
        <p className="text-text-secondary leading-relaxed">
          The Dearth Score is a composite metric (0-100) that quantifies the
          severity of healthcare provider shortages in a US county for a given
          medical specialty. A higher score indicates worse healthcare access.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Methodology
        </h2>
        <p className="text-text-secondary leading-relaxed">
          The score is calculated per (county, specialty) pair using four
          components, each normalized via percentile ranking across all counties:
        </p>
        <ol className="list-decimal ml-6 space-y-2 text-text-secondary">
          <li>
            <strong className="text-text-primary">
              Provider Density (40%)
            </strong>{" "}
            &mdash; Providers per 100,000 population. Higher density = better
            access. Score = 100 &times; (1 - percentile rank of density).
          </li>
          <li>
            <strong className="text-text-primary">
              Distance to Care (30%)
            </strong>{" "}
            &mdash; Average distance (miles) to the nearest 3 providers from the
            county centroid. Score = 100 &times; percentile rank of distance.
          </li>
          <li>
            <strong className="text-text-primary">Drive Time (20%)</strong>{" "}
            &mdash; Estimated drive time to the nearest provider. Currently
            approximated as 1.5 &times; distance for MVP. Score = min(100, drive
            time proxy).
          </li>
          <li>
            <strong className="text-text-primary">Wait Time (10%)</strong>{" "}
            &mdash; Average appointment wait time in days. Currently set to a
            default of 50 (score) pending real data integration.
          </li>
        </ol>
        <div className="bg-surface-700/60 rounded-lg p-4 mt-4">
          <p className="font-mono text-sm text-text-primary">
            Dearth Score = 0.4 &times; Density Score + 0.3 &times; Distance
            Score + 0.2 &times; DriveTime Score + 0.1 &times; WaitTime Score
          </p>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Score Interpretation
        </h2>
        <div className="border border-white/[0.06] rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-700/80">
              <tr>
                <th className="text-left px-4 py-2 text-text-muted">
                  Score Range
                </th>
                <th className="text-left px-4 py-2 text-text-muted">Label</th>
                <th className="text-left px-4 py-2 text-text-muted">
                  Interpretation
                </th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-white/[0.06]">
                <td className="px-4 py-2 text-text-primary">
                  <span
                    className="inline-block w-3 h-3 rounded mr-2"
                    style={{ backgroundColor: "#22c55e" }}
                  />
                  0 - 20
                </td>
                <td className="px-4 py-2 text-text-primary">Well Served</td>
                <td className="px-4 py-2 text-text-secondary">
                  Provider supply meets or exceeds needs
                </td>
              </tr>
              <tr className="border-t border-white/[0.06]">
                <td className="px-4 py-2 text-text-primary">
                  <span
                    className="inline-block w-3 h-3 rounded mr-2"
                    style={{ backgroundColor: "#84cc16" }}
                  />
                  21 - 40
                </td>
                <td className="px-4 py-2 text-text-primary">Adequate</td>
                <td className="px-4 py-2 text-text-secondary">
                  Minor gaps in provider availability
                </td>
              </tr>
              <tr className="border-t border-white/[0.06]">
                <td className="px-4 py-2 text-text-primary">
                  <span
                    className="inline-block w-3 h-3 rounded mr-2"
                    style={{ backgroundColor: "#f59e0b" }}
                  />
                  41 - 60
                </td>
                <td className="px-4 py-2 text-text-primary">
                  Moderate Shortage
                </td>
                <td className="px-4 py-2 text-text-secondary">
                  Notable provider shortages affecting access
                </td>
              </tr>
              <tr className="border-t border-white/[0.06]">
                <td className="px-4 py-2 text-text-primary">
                  <span
                    className="inline-block w-3 h-3 rounded mr-2"
                    style={{ backgroundColor: "#f97316" }}
                  />
                  61 - 80
                </td>
                <td className="px-4 py-2 text-text-primary">
                  Significant Shortage
                </td>
                <td className="px-4 py-2 text-text-secondary">
                  Significant provider shortages across the specialty
                </td>
              </tr>
              <tr className="border-t border-white/[0.06]">
                <td className="px-4 py-2 text-text-primary">
                  <span
                    className="inline-block w-3 h-3 rounded mr-2"
                    style={{ backgroundColor: "#ef4444" }}
                  />
                  81 - 100
                </td>
                <td className="px-4 py-2 text-text-primary">
                  Severe Shortage
                </td>
                <td className="px-4 py-2 text-text-secondary">
                  Healthcare desert with very few or no providers
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Specialties Covered
        </h2>
        <p className="text-text-secondary leading-relaxed">
          The map tracks 15 medical specialties: Primary Care, Cardiology,
          Neurology, Nephrology, Oncology, Psychiatry, OB/GYN, Orthopedics,
          General Surgery, Emergency Medicine, Radiology, Pathology, Dermatology,
          Ophthalmology, and Pediatrics.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Data Sources
        </h2>
        <ul className="list-disc ml-6 space-y-1 text-text-secondary">
          <li>
            <strong className="text-text-primary">Provider data:</strong> CMS
            National Plan and Provider Enumeration System (NPPES / NPI Registry)
          </li>
          <li>
            <strong className="text-text-primary">Population data:</strong> US
            Census Bureau American Community Survey (ACS)
          </li>
          <li>
            <strong className="text-text-primary">County boundaries:</strong> US
            Census Bureau TIGER/Line shapefiles
          </li>
          <li>
            <strong className="text-text-primary">Validation:</strong> HRSA
            Health Professional Shortage Area (HPSA) designations
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Limitations
        </h2>
        <ul className="list-disc ml-6 space-y-1 text-text-secondary">
          <li>
            Provider counts are based on NPPES data and may not reflect
            current practice status for all providers.
          </li>
          <li>
            Provider counts are based on practice location, not where patients
            actually receive care.
          </li>
          <li>
            The model does not account for telehealth availability or
            cross-county care patterns.
          </li>
        </ul>
      </section>
    </div>
  );
}

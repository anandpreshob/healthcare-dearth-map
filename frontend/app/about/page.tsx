export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <h1 className="text-3xl font-bold">About the Healthcare Dearth Map</h1>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">What is a Dearth Score?</h2>
        <p className="text-gray-700 leading-relaxed">
          The Dearth Score is a composite metric (0-100) that quantifies the
          severity of healthcare provider shortages in a US county for a given
          medical specialty. A higher score indicates worse healthcare access.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Methodology</h2>
        <p className="text-gray-700 leading-relaxed">
          The score is calculated per (county, specialty) pair using four
          components, each normalized via percentile ranking across all counties:
        </p>
        <ol className="list-decimal ml-6 space-y-2 text-gray-700">
          <li>
            <strong>Provider Density (40%)</strong> &mdash; Providers per 100,000
            population. Higher density = better access. Score = 100 &times; (1 -
            percentile rank of density).
          </li>
          <li>
            <strong>Distance to Care (30%)</strong> &mdash; Average distance (miles)
            to the nearest 3 providers from the county centroid. Score = 100 &times;
            percentile rank of distance.
          </li>
          <li>
            <strong>Drive Time (20%)</strong> &mdash; Estimated drive time to the
            nearest provider. Currently approximated as 1.5 &times; distance for MVP.
            Score = min(100, drive time proxy).
          </li>
          <li>
            <strong>Wait Time (10%)</strong> &mdash; Average appointment wait time
            in days. Currently set to a default of 50 (score) pending real data
            integration.
          </li>
        </ol>
        <div className="bg-gray-50 rounded-lg p-4 mt-4">
          <p className="font-mono text-sm text-gray-800">
            Dearth Score = 0.4 &times; Density Score + 0.3 &times; Distance Score +
            0.2 &times; DriveTime Score + 0.1 &times; WaitTime Score
          </p>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Score Interpretation</h2>
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-2">Score Range</th>
                <th className="text-left px-4 py-2">Label</th>
                <th className="text-left px-4 py-2">Interpretation</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t">
                <td className="px-4 py-2">
                  <span className="inline-block w-3 h-3 rounded mr-2" style={{ backgroundColor: "#1a9850" }} />
                  0 - 20
                </td>
                <td className="px-4 py-2">Well Served</td>
                <td className="px-4 py-2 text-gray-600">
                  Provider supply meets or exceeds needs
                </td>
              </tr>
              <tr className="border-t">
                <td className="px-4 py-2">
                  <span className="inline-block w-3 h-3 rounded mr-2" style={{ backgroundColor: "#91cf60" }} />
                  21 - 40
                </td>
                <td className="px-4 py-2">Adequate</td>
                <td className="px-4 py-2 text-gray-600">
                  Minor gaps in provider availability
                </td>
              </tr>
              <tr className="border-t">
                <td className="px-4 py-2">
                  <span className="inline-block w-3 h-3 rounded mr-2" style={{ backgroundColor: "#fee08b" }} />
                  41 - 60
                </td>
                <td className="px-4 py-2">Moderate Shortage</td>
                <td className="px-4 py-2 text-gray-600">
                  Notable provider shortages affecting access
                </td>
              </tr>
              <tr className="border-t">
                <td className="px-4 py-2">
                  <span className="inline-block w-3 h-3 rounded mr-2" style={{ backgroundColor: "#fc8d59" }} />
                  61 - 80
                </td>
                <td className="px-4 py-2">Significant Shortage</td>
                <td className="px-4 py-2 text-gray-600">
                  Significant provider shortages across the specialty
                </td>
              </tr>
              <tr className="border-t">
                <td className="px-4 py-2">
                  <span className="inline-block w-3 h-3 rounded mr-2" style={{ backgroundColor: "#d73027" }} />
                  81 - 100
                </td>
                <td className="px-4 py-2">Severe Shortage</td>
                <td className="px-4 py-2 text-gray-600">
                  Healthcare desert with very few or no providers
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Specialties Covered</h2>
        <p className="text-gray-700 leading-relaxed">
          The map tracks 15 medical specialties: Primary Care, Cardiology,
          Neurology, Nephrology, Oncology, Psychiatry, OB/GYN, Orthopedics,
          General Surgery, Emergency Medicine, Radiology, Pathology, Dermatology,
          Ophthalmology, and Pediatrics.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Data Sources</h2>
        <ul className="list-disc ml-6 space-y-1 text-gray-700">
          <li>
            <strong>Provider data:</strong> CMS National Plan and Provider
            Enumeration System (NPPES / NPI Registry)
          </li>
          <li>
            <strong>Population data:</strong> US Census Bureau American
            Community Survey (ACS)
          </li>
          <li>
            <strong>County boundaries:</strong> US Census Bureau TIGER/Line
            shapefiles
          </li>
          <li>
            <strong>Validation:</strong> HRSA Health Professional Shortage Area
            (HPSA) designations
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Limitations</h2>
        <ul className="list-disc ml-6 space-y-1 text-gray-700">
          <li>
            Currently uses sample data for 5 states (CA, TX, NY, MS, MT) with
            approximately 200 counties. Full national coverage is planned.
          </li>
          <li>
            Drive time is approximated as 1.5x distance. Real routing integration
            (OSRM/Google Maps) is planned.
          </li>
          <li>
            Wait time data is not yet available and uses a default value.
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

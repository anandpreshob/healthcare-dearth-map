export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      <h1 className="text-3xl font-bold text-text-primary">
        About the Healthcare Dearth Map
      </h1>

      {/* Overview */}
      <section className="space-y-3">
        <p className="text-text-secondary leading-relaxed">
          The Healthcare Dearth Map is an interactive tool that visualizes
          healthcare access gaps across all 3,109 counties in the contiguous
          United States. It covers 15 medical specialties and uses a composite{" "}
          <strong className="text-text-primary">Dearth Score</strong> (0&ndash;100)
          to quantify how underserved each county is &mdash; higher means worse
          access. The map is designed for health policy researchers, healthcare
          planners, and anyone interested in understanding where provider
          shortages are most severe.
        </p>
      </section>

      {/* How it was built */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          How It Was Built
        </h2>
        <p className="text-text-secondary leading-relaxed">
          The application was built as a data pipeline that processes publicly
          available federal datasets, computes access metrics using spatial
          algorithms and road-network routing, and exports the results as static
          files served on GitHub Pages &mdash; no backend server required.
        </p>
        <ol className="list-decimal ml-6 space-y-3 text-text-secondary">
          <li>
            <strong className="text-text-primary">Provider data collection</strong>
            &nbsp;&mdash; We downloaded the full{" "}
            <a
              href="https://download.cms.gov/nppes/NPI_Files.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              NPPES National Provider Registry
            </a>{" "}
            (9.7 GB), filtered to 1,560,696 active individual providers, and
            mapped their 139 NPI taxonomy codes to 15 specialty categories.
          </li>
          <li>
            <strong className="text-text-primary">Geographic data</strong>
            &nbsp;&mdash; County boundaries, centroids, and populations come from
            the{" "}
            <a
              href="https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              US Census Bureau Gazetteer files
            </a>
            . We used the Census ZCTA-to-county crosswalk to map 33,012 zip code
            tabulation areas to their primary counties.
          </li>
          <li>
            <strong className="text-text-primary">Spatial analysis</strong>
            &nbsp;&mdash; Using PostGIS spatial queries, we computed provider
            counts, density (per 100k population), and nearest-provider
            distances for every county-specialty pair.
          </li>
          <li>
            <strong className="text-text-primary">Drive time computation</strong>
            &nbsp;&mdash; We processed the full US road network from{" "}
            <a
              href="https://download.geofabrik.de/north-america.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              OpenStreetMap (Geofabrik)
            </a>{" "}
            using{" "}
            <a
              href="https://project-osrm.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              OSRM (Open Source Routing Machine)
            </a>{" "}
            to calculate actual road-network drive times from each county
            centroid to its nearest provider for every specialty.
          </li>
          <li>
            <strong className="text-text-primary">Score calculation</strong>
            &nbsp;&mdash; Each metric was percentile-ranked across all counties
            within each specialty, then combined into a weighted composite
            Dearth Score. Scores were validated against{" "}
            <a
              href="https://data.hrsa.gov/topics/health-workforce/shortage-areas"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              HRSA Health Professional Shortage Area (HPSA)
            </a>{" "}
            designations.
          </li>
          <li>
            <strong className="text-text-primary">
              Enrichment data integration
            </strong>
            &nbsp;&mdash; We layer in additional public data sources to provide
            a more complete picture of healthcare access: Medicare participation
            rates from the{" "}
            <a
              href="https://data.cms.gov/provider-data/dataset/mj5m-pzi6"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              CMS Care Compare
            </a>{" "}
            database, emergency department wait times from{" "}
            <a
              href="https://data.cms.gov/provider-data/topics/hospitals/timely-effective-care"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              CMS Hospital Compare
            </a>
            , and community health center locations from{" "}
            <a
              href="https://data.hrsa.gov/topics/health-centers"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              HRSA
            </a>
            .
          </li>
        </ol>
      </section>

      {/* Dearth Score */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          The Dearth Score
        </h2>
        <p className="text-text-secondary leading-relaxed">
          The Dearth Score is calculated per county-specialty pair using two
          components, each normalized via percentile ranking across all 3,109
          counties:
        </p>
        <ol className="list-decimal ml-6 space-y-2 text-text-secondary">
          <li>
            <strong className="text-text-primary">
              Provider Density (60%)
            </strong>{" "}
            &mdash; Number of providers per 100,000 population. Higher density
            means better access. Score = 100 &times; (1 &minus; percentile rank
            of density). A county in the bottom percentile for provider density
            scores close to 100.
          </li>
          <li>
            <strong className="text-text-primary">
              Drive Time (40%)
            </strong>{" "}
            &mdash; Road-network drive time (in minutes) from the county
            centroid to the nearest provider, computed using OSRM with real
            OpenStreetMap road data. Score = 100 &times; percentile rank of
            drive time. A county with the longest drive time scores close to 100.
          </li>
        </ol>
        <div className="bg-surface-700/60 rounded-lg p-4 mt-4">
          <p className="font-mono text-sm text-text-primary">
            Dearth Score = 0.6 &times; Density Score + 0.4 &times; Drive Time
            Score
          </p>
        </div>
        <p className="text-text-secondary leading-relaxed text-sm mt-2">
          Density is weighted higher (60%) because a county can have a short
          drive to one provider who serves 200,000 people &mdash; the proximity
          alone doesn&apos;t mean the area is well served. Drive time (40%)
          captures geographic accessibility through real road networks, which
          matters most in rural areas where the nearest specialist may be hours
          away through mountain roads or across rivers.
        </p>
      </section>

      {/* Score table */}
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
                  0 &ndash; 20
                </td>
                <td className="px-4 py-2 text-text-primary">Well Served</td>
                <td className="px-4 py-2 text-text-secondary">
                  Provider supply meets or exceeds community needs
                </td>
              </tr>
              <tr className="border-t border-white/[0.06]">
                <td className="px-4 py-2 text-text-primary">
                  <span
                    className="inline-block w-3 h-3 rounded mr-2"
                    style={{ backgroundColor: "#84cc16" }}
                  />
                  21 &ndash; 40
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
                  41 &ndash; 60
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
                  61 &ndash; 80
                </td>
                <td className="px-4 py-2 text-text-primary">
                  Significant Shortage
                </td>
                <td className="px-4 py-2 text-text-secondary">
                  Severe provider gaps; residents may travel long distances
                </td>
              </tr>
              <tr className="border-t border-white/[0.06]">
                <td className="px-4 py-2 text-text-primary">
                  <span
                    className="inline-block w-3 h-3 rounded mr-2"
                    style={{ backgroundColor: "#ef4444" }}
                  />
                  81 &ndash; 100
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

      {/* Specialties */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Specialties Covered
        </h2>
        <p className="text-text-secondary leading-relaxed">
          The map tracks 15 medical specialties, covering 139 NPI taxonomy codes:
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-2">
          {[
            "Primary Care",
            "Cardiology",
            "Neurology",
            "Nephrology",
            "Oncology",
            "Psychiatry",
            "OB/GYN",
            "Orthopedics",
            "General Surgery",
            "Emergency Medicine",
            "Radiology",
            "Pathology",
            "Dermatology",
            "Ophthalmology",
            "Pediatrics",
          ].map((name) => (
            <div
              key={name}
              className="px-3 py-1.5 rounded-lg bg-surface-700/60 text-sm text-text-secondary"
            >
              {name}
            </div>
          ))}
        </div>
      </section>

      {/* Data sources */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Data Sources
        </h2>
        <ul className="list-disc ml-6 space-y-2 text-text-secondary">
          <li>
            <strong className="text-text-primary">Provider data:</strong>{" "}
            <a
              href="https://download.cms.gov/nppes/NPI_Files.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              CMS NPPES National Provider Registry
            </a>{" "}
            &mdash; 1,560,696 active individual providers with practice
            locations and taxonomy codes
          </li>
          <li>
            <strong className="text-text-primary">Population &amp; geography:</strong>{" "}
            <a
              href="https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              US Census Bureau Gazetteer files
            </a>{" "}
            &mdash; County and ZCTA centroids, populations, and land areas
          </li>
          <li>
            <strong className="text-text-primary">Road network:</strong>{" "}
            <a
              href="https://download.geofabrik.de/north-america.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              OpenStreetMap via Geofabrik
            </a>{" "}
            &mdash; US road network processed with OSRM for drive time routing
          </li>
          <li>
            <strong className="text-text-primary">Medicare participation:</strong>{" "}
            <a
              href="https://data.cms.gov/provider-data/dataset/mj5m-pzi6"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              CMS Care Compare (DAC National Downloadable File)
            </a>{" "}
            &mdash; Medicare assignment acceptance, EHR participation, and
            quality measure reporting for individual clinicians
          </li>
          <li>
            <strong className="text-text-primary">ED wait times:</strong>{" "}
            <a
              href="https://data.cms.gov/provider-data/topics/hospitals/timely-effective-care"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              CMS Hospital Compare &mdash; Timely &amp; Effective Care
            </a>{" "}
            &mdash; Hospital-level emergency department wait time measures
            (OP-18, ED-1) aggregated to county level
          </li>
          <li>
            <strong className="text-text-primary">Community health centers:</strong>{" "}
            <a
              href="https://data.hrsa.gov/topics/health-centers"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              HRSA Health Center Service Delivery Sites
            </a>{" "}
            &mdash; Federally Qualified Health Centers (FQHCs) and Look-Alike
            sites that serve underserved populations regardless of ability to pay
          </li>
          <li>
            <strong className="text-text-primary">Validation:</strong>{" "}
            <a
              href="https://data.hrsa.gov/topics/health-workforce/shortage-areas"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              HRSA Health Professional Shortage Area (HPSA)
            </a>{" "}
            designations used to validate score accuracy
          </li>
        </ul>
      </section>

      {/* Data stats */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          By the Numbers
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { value: "3,109", label: "Counties" },
            { value: "15", label: "Specialties" },
            { value: "1.56M", label: "Providers" },
            { value: "46,635", label: "Dearth Scores" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="bg-surface-700/60 rounded-lg p-3 text-center"
            >
              <div className="text-xl font-bold text-text-primary">
                {stat.value}
              </div>
              <div className="text-xs text-text-muted mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Limitations */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Current Limitations
        </h2>
        <ul className="list-disc ml-6 space-y-2 text-text-secondary">
          <li>
            <strong className="text-text-primary">NPPES data currency</strong>
            &nbsp;&mdash; Provider counts are based on NPPES registry data, which
            may not reflect whether a listed provider is actively seeing patients
            or has retired.
          </li>
          <li>
            <strong className="text-text-primary">Practice location only</strong>
            &nbsp;&mdash; Providers are counted at their registered practice
            address. The model does not account for providers who serve multiple
            locations or cross-county patient flows.
          </li>
          <li>
            <strong className="text-text-primary">Limited wait time data</strong>
            &nbsp;&mdash; We include hospital emergency department wait times
            from CMS, but appointment wait times for outpatient visits (e.g.,
            weeks to see a specialist) are not available from any reliable
            nationwide public data source.
          </li>
          <li>
            <strong className="text-text-primary">No telehealth</strong>
            &nbsp;&mdash; The model does not account for telehealth availability,
            which may improve access in underserved areas without requiring
            physical proximity.
          </li>
          <li>
            <strong className="text-text-primary">County-level granularity</strong>
            &nbsp;&mdash; Scores are computed at the county level. Access can vary
            significantly within large counties, especially in urban areas.
          </li>
          <li>
            <strong className="text-text-primary">Drive time from centroid</strong>
            &nbsp;&mdash; Drive times are measured from the county geographic
            centroid, which may not represent where most residents live,
            particularly in large or irregularly shaped counties.
          </li>
        </ul>
      </section>

      {/* Future improvements */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Planned Improvements
        </h2>

        <h3 className="text-base font-semibold text-text-primary mt-4">
          Data Enrichment
        </h3>
        <ul className="list-disc ml-6 space-y-2 text-text-secondary">
          <li>
            <strong className="text-text-primary">
              Insurance network coverage
            </strong>
            &nbsp;&mdash; Parse machine-readable provider directory files that
            insurers are required to publish under the Transparency in Coverage
            Rule. Starting with the top 5 insurers by market share (UnitedHealth,
            Anthem, Aetna, Cigna, Humana) to compute per-county insurance network
            coverage rates.
          </li>
          <li>
            <strong className="text-text-primary">
              New patient acceptance status
            </strong>
            &nbsp;&mdash; Enrich provider records using targeted web scraping of
            aggregator sites (Healthgrades, Vitals, WebMD) via the Brave Search
            API. Prioritized for providers in high-dearth-score counties to
            maximize impact per query.
          </li>
          <li>
            <strong className="text-text-primary">
              Appointment wait time estimation
            </strong>
            &nbsp;&mdash; Incorporate Merritt Hawkins annual survey data for
            specialty-level metro averages, supplemented by HCAHPS patient
            experience survey data. Long-term: build a predictive model using
            provider density, drive time, specialty, and urbanicity as features.
          </li>
          <li>
            <strong className="text-text-primary">
              State Medicaid provider directories
            </strong>
            &nbsp;&mdash; Ingest state-level Medicaid provider enrollment files
            (available as public CSVs from most state Medicaid agencies) to
            compute Medicaid acceptance rates by county.
          </li>
        </ul>

        <h3 className="text-base font-semibold text-text-primary mt-4">
          Analysis &amp; Visualization
        </h3>
        <ul className="list-disc ml-6 space-y-2 text-text-secondary">
          <li>
            <strong className="text-text-primary">
              Real-time drive times via Google Maps API
            </strong>
            &nbsp;&mdash; Replace OSRM static routing with Google Maps Distance
            Matrix API for real-time drive times that account for current traffic
            conditions, road closures, and construction.
          </li>
          <li>
            <strong className="text-text-primary">
              Sub-county visualization
            </strong>
            &nbsp;&mdash; Drill down to zip code level within counties for more
            granular analysis, particularly useful in urban areas where access
            can vary block-by-block.
          </li>
          <li>
            <strong className="text-text-primary">
              Telehealth overlay
            </strong>
            &nbsp;&mdash; Layer in FCC broadband availability data to identify
            where telehealth could bridge physical access gaps, and estimate the
            impact on effective Dearth Scores.
          </li>
          <li>
            <strong className="text-text-primary">
              Trend analysis
            </strong>
            &nbsp;&mdash; Track changes over time using monthly NPPES updates to
            identify areas where provider shortages are worsening or improving,
            enabling longitudinal studies of healthcare desertification.
          </li>
          <li>
            <strong className="text-text-primary">
              Multi-factor Dearth Score
            </strong>
            &nbsp;&mdash; Expand the composite score to incorporate Medicare
            acceptance rates, ED wait times, health center availability, and
            insurance coverage as weighted components alongside density and
            drive time.
          </li>
        </ul>

        <h3 className="text-base font-semibold text-text-primary mt-4">
          Data Collection Strategy
        </h3>
        <p className="text-text-secondary leading-relaxed text-sm">
          This project exclusively uses publicly available, open-source data.
          Our strategy for additional data collection follows a tiered approach:
        </p>
        <ul className="list-disc ml-6 space-y-2 text-text-secondary text-sm">
          <li>
            <strong className="text-text-primary">Tier 1 (Bulk public data):</strong>{" "}
            CMS Care Compare, HCAHPS, HRSA health center data &mdash; free
            bulk downloads joined by NPI or geography.
          </li>
          <li>
            <strong className="text-text-primary">Tier 2 (Mandated transparency files):</strong>{" "}
            Machine-readable insurer provider directories required by CMS
            &mdash; published as JSON/CSV by all major insurers.
          </li>
          <li>
            <strong className="text-text-primary">Tier 3 (Targeted web enrichment):</strong>{" "}
            Brave Search API + provider aggregator scraping for new patient
            status and insurance acceptance, prioritized for underserved areas.
          </li>
          <li>
            <strong className="text-text-primary">Tier 4 (Modeled estimates):</strong>{" "}
            Statistical models combining survey data (Merritt Hawkins, HCAHPS)
            with provider density and geographic features to estimate metrics
            where direct data is unavailable.
          </li>
        </ul>
      </section>

      {/* Disclaimer */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-text-primary">
          Disclaimer
        </h2>
        <div className="bg-surface-700/60 rounded-lg p-4 border border-white/[0.06]">
          <p className="text-text-secondary leading-relaxed text-sm">
            <strong className="text-text-primary">
              For research and educational purposes only.
            </strong>{" "}
            The Healthcare Dearth Map is not a substitute for professional
            medical advice, diagnosis, or treatment. The Dearth Scores and
            visualizations are derived from publicly available datasets and
            computational models that may not reflect current real-world
            conditions, including whether listed providers are actively
            practicing, accepting new patients, or participating in specific
            insurance networks.
          </p>
          <p className="text-text-secondary leading-relaxed text-sm mt-3">
            The authors make no representations or warranties regarding the
            accuracy, completeness, or reliability of the data, scores, or
            visualizations. Users should not make healthcare, policy, or
            business decisions based solely on this tool without independent
            verification. Use of this software is at your own risk.
          </p>
        </div>
      </section>

      {/* License & Credits */}
      <section className="space-y-3 pb-8">
        <h2 className="text-xl font-semibold text-text-primary">
          Open Source &amp; License
        </h2>
        <p className="text-text-secondary leading-relaxed">
          This project is open source under the{" "}
          <a
            href="https://github.com/anandpreshob/healthcare-dearth-map/blob/main/LICENSE"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            MIT License
          </a>
          . You are free to use, modify, and distribute the code and data with
          attribution. The full codebase, including the ETL pipeline, data
          export scripts, and frontend application, is available on{" "}
          <a
            href="https://github.com/anandpreshob/healthcare-dearth-map"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            GitHub
          </a>
          .
        </p>
      </section>
    </div>
  );
}

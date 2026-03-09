"""ETL pipeline orchestrator.

Connects to the database and runs:
1.  download_data       - download NPPES, Census, CMS, HRSA files to SSD
2.  load_counties       - parse Census Gazetteer + population -> counties table
3.  load_zipcodes       - parse ZCTA Gazetteer + crosswalk -> zipcodes table
4.  load_providers      - parse NPPES CSV (chunked) -> providers table
5.  compute_metrics     - calculate per-county provider metrics
6.  compute_drivetimes  - query OSRM for actual drive times (optional)
7.  compute_scores      - compute dearth scores from metrics
8.  load_cms_care_compare   - CMS DAC Medicare participation data
9.  load_hcahps             - CMS Hospital ED wait times
10. load_hrsa_health_centers - HRSA community health center sites
11. compute_enrichment      - aggregate enrichment data at county level
"""

import argparse
import time

import psycopg2

from .config import get_db_params
from . import download_data
from . import load_counties
from . import load_zipcodes
from . import load_providers
from . import compute_metrics
from . import compute_drivetimes
from . import compute_scores
from . import load_cms_care_compare
from . import load_hcahps
from . import load_hrsa_health_centers
from . import compute_enrichment


def run(skip_download: bool = False, skip_drivetimes: bool = False,
        skip_enrichment: bool = False):
    """Execute the full ETL pipeline."""
    print("=" * 60)
    print("Healthcare Dearth Map - Real Data ETL Pipeline")
    print("=" * 60)
    start = time.time()

    # Step 1: Download data files
    if not skip_download:
        download_data.run()
    else:
        print("[SKIP] Data download (--skip-download)")

    # Step 2-11: Database operations
    db_params = get_db_params()
    print(f"Connecting to database: {db_params['dbname']}@{db_params['host']}:{db_params['port']}")

    conn = psycopg2.connect(**db_params)
    try:
        # Step 2: Load counties
        load_counties.run(conn)

        # Step 3: Load ZCTAs
        load_zipcodes.run(conn)

        # Step 4: Load providers from NPPES
        load_providers.run(conn)

        # Step 5: Compute metrics
        compute_metrics.run(conn)

        # Step 6: Compute drive times via OSRM
        if not skip_drivetimes:
            compute_drivetimes.run(conn)
        else:
            print("[SKIP] Drive time computation (--skip-drivetimes)")

        # Step 7: Compute dearth scores
        compute_scores.run(conn)

        # Steps 8-11: Enrichment data (CMS + HRSA)
        if not skip_enrichment:
            # Step 8: CMS Care Compare (Medicare participation)
            load_cms_care_compare.run(conn)

            # Step 9: CMS Hospital Timely Care (ED wait times)
            load_hcahps.run(conn)

            # Step 10: HRSA Health Centers
            load_hrsa_health_centers.run(conn)

            # Step 11: Aggregate enrichment at county level
            compute_enrichment.run(conn)
        else:
            print("[SKIP] Enrichment data (--skip-enrichment)")

    finally:
        conn.close()

    elapsed = time.time() - start
    print("=" * 60)
    print(f"ETL Pipeline Complete! ({elapsed:.0f}s)")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Healthcare Dearth Map ETL pipeline")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading data files (use existing files on SSD)",
    )
    parser.add_argument(
        "--skip-drivetimes",
        action="store_true",
        help="Skip OSRM drive time computation (use proxy values)",
    )
    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Skip CMS/HRSA enrichment data loading",
    )
    args = parser.parse_args()
    run(
        skip_download=args.skip_download,
        skip_drivetimes=args.skip_drivetimes,
        skip_enrichment=args.skip_enrichment,
    )

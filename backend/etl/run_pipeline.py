"""ETL pipeline orchestrator.

Connects to the database and runs:
1. download_data - download NPPES, Census files to SSD
2. load_counties - parse Census Gazetteer + population -> counties table
3. load_zipcodes - parse ZCTA Gazetteer + crosswalk -> zipcodes table
4. load_providers - parse NPPES CSV (chunked) -> providers table
5. compute_metrics - calculate per-county provider metrics
6. compute_scores - compute dearth scores from metrics
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
from . import compute_scores


def run(skip_download: bool = False):
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

    # Step 2-6: Database operations
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

        # Step 6: Compute dearth scores
        compute_scores.run(conn)

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
    args = parser.parse_args()
    run(skip_download=args.skip_download)

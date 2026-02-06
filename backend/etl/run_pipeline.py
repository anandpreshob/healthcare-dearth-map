"""ETL pipeline orchestrator.

Connects to the database and runs:
1. generate_sample_data - populate counties, zipcodes, providers
2. compute_metrics - calculate per-county provider metrics
3. compute_scores - compute dearth scores from metrics
"""

import psycopg2
from .config import get_db_params
from . import generate_sample_data
from . import compute_metrics
from . import compute_scores


def run():
    """Execute the full ETL pipeline."""
    print("=" * 60)
    print("Healthcare Dearth Map - ETL Pipeline")
    print("=" * 60)

    db_params = get_db_params()
    print(f"Connecting to database: {db_params['dbname']}@{db_params['host']}:{db_params['port']}")

    conn = psycopg2.connect(**db_params)
    try:
        # Step 1: Generate sample data
        generate_sample_data.run(conn)

        # Step 2: Compute metrics
        compute_metrics.run(conn)

        # Step 3: Compute dearth scores
        compute_scores.run(conn)

        print("=" * 60)
        print("ETL Pipeline Complete!")
        print("=" * 60)
    finally:
        conn.close()


if __name__ == "__main__":
    run()

"""Load ZCTAs (zip code tabulation areas) from Census data.

Input files:
  - ZCTA Gazetteer (2023_Gaz_zcta_national.txt) - centroids
  - ZCTA-County Crosswalk (tab20_zcta520_county20_natl.txt) - ZCTA-to-county mapping

Output: ~33,000 rows in the `zipcodes` table.
"""

import csv
import os

from psycopg2.extras import execute_values

from .config import RAW_DIR
from .download_data import get_zcta_gazetteer_path
from .state_fips import CONUS_STATE_FIPS


def _load_zcta_centroids() -> dict[str, tuple[float, float]]:
    """Parse ZCTA Gazetteer -> dict of ZCTA -> (lat, lon)."""
    path = get_zcta_gazetteer_path()
    centroids = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        reader.fieldnames = [fn.strip() for fn in reader.fieldnames]
        for row in reader:
            zcta = row["GEOID"].strip()
            lat_str = row["INTPTLAT"].strip()
            lon_str = row["INTPTLONG"].strip()
            if lat_str and lon_str:
                centroids[zcta] = (float(lat_str), float(lon_str))
    return centroids


def _load_crosswalk() -> dict[str, str]:
    """Parse ZCTA-County crosswalk -> dict of ZCTA -> county FIPS.

    When a ZCTA spans multiple counties, use the one with the largest
    land area overlap (AREALAND_PART).
    """
    path = os.path.join(RAW_DIR, "tab20_zcta520_county20_natl.txt")
    # Track best county per ZCTA by area
    best: dict[str, tuple[str, int]] = {}  # zcta -> (county_fips, area)

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            zcta = row["GEOID_ZCTA5_20"].strip()
            county_fips = row["GEOID_COUNTY_20"].strip()
            area_str = row.get("AREALAND_PART", "0").strip()
            area = int(area_str) if area_str else 0

            if zcta not in best or area > best[zcta][1]:
                best[zcta] = (county_fips, area)

    return {zcta: county_fips for zcta, (county_fips, _) in best.items()}


def run(conn):
    """Load ZCTAs into the zipcodes table."""
    print("=== Loading ZCTAs (Zipcodes) ===")

    centroids = _load_zcta_centroids()
    print(f"  Parsed {len(centroids)} ZCTA centroids")

    crosswalk = _load_crosswalk()
    print(f"  Parsed {len(crosswalk)} ZCTA-county mappings")

    # Get valid county FIPS from DB
    with conn.cursor() as cur:
        cur.execute("SELECT fips FROM counties")
        valid_counties = {row[0] for row in cur.fetchall()}
    print(f"  {len(valid_counties)} valid counties in DB")

    # Build insert rows: only ZCTAs that map to valid CONUS counties
    rows = []
    for zcta, (lat, lon) in centroids.items():
        county_fips = crosswalk.get(zcta)
        if not county_fips or county_fips not in valid_counties:
            continue
        state_fips = county_fips[:2]
        if state_fips not in CONUS_STATE_FIPS:
            continue
        from .state_fips import STATE_FIPS
        abbr = STATE_FIPS[state_fips][0]
        rows.append((
            zcta,
            county_fips,
            abbr,
            None,  # population - not critical for this pipeline
            None,  # land_area_sqmi
            f"SRID=4326;POINT({lon} {lat})",
        ))

    print(f"  Inserting {len(rows)} ZCTAs...")
    with conn.cursor() as cur:
        cur.execute("DELETE FROM zipcodes")
        conn.commit()

        # Batch insert
        batch_size = 5000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            execute_values(
                cur,
                """INSERT INTO zipcodes (zcta, county_fips, state_abbr,
                   population, land_area_sqmi, centroid)
                   VALUES %s ON CONFLICT (zcta) DO UPDATE SET
                     county_fips = EXCLUDED.county_fips,
                     centroid = EXCLUDED.centroid""",
                batch,
                template="(%s, %s, %s, %s, %s, ST_GeomFromEWKT(%s))",
            )
        conn.commit()

    print(f"  Loaded {len(rows)} ZCTAs")
    print("=== ZCTA Load Complete ===")


if __name__ == "__main__":
    import psycopg2
    from .config import get_db_params
    conn = psycopg2.connect(**get_db_params())
    try:
        run(conn)
    finally:
        conn.close()

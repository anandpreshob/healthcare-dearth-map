"""Load all continental US counties from Census data.

Input files:
  - Census County Gazetteer (2023_Gaz_counties_national.txt)
  - Census Population Estimates (co-est2023-alldata.csv)

Output: ~3,143 rows in the `counties` table.
"""

import csv
import os

from psycopg2.extras import execute_values

from .config import RAW_DIR
from .download_data import get_county_gazetteer_path, get_population_csv_path
from .state_fips import STATE_FIPS, CONUS_STATE_FIPS


def _load_gazetteer() -> dict[str, dict]:
    """Parse Census County Gazetteer -> dict keyed by 5-digit FIPS."""
    path = get_county_gazetteer_path()
    counties = {}
    with open(path, "r", encoding="utf-8") as f:
        # Tab-separated with header row; strip keys (Census files have trailing whitespace)
        reader = csv.DictReader(f, delimiter="\t")
        reader.fieldnames = [fn.strip() for fn in reader.fieldnames]
        for row in reader:
            geoid = row["GEOID"].strip()
            state_fips = geoid[:2]
            if state_fips not in CONUS_STATE_FIPS:
                continue
            abbr, name = STATE_FIPS[state_fips]
            area_str = row.get("ALAND_SQMI", "").strip()
            counties[geoid] = {
                "fips": geoid,
                "name": row["NAME"].strip(),
                "state_fips": state_fips,
                "state_abbr": abbr,
                "state_name": name,
                "lat": float(row["INTPTLAT"].strip()),
                "lon": float(row["INTPTLONG"].strip()),
                "land_area_sqmi": float(area_str) if area_str else 0.0,
            }
    return counties


def _load_population() -> dict[str, int]:
    """Parse Census population estimates -> dict of FIPS -> population."""
    path = get_population_csv_path()
    populations = {}
    with open(path, "r", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            state_fips = row["STATE"].strip().zfill(2)
            county_fips = row["COUNTY"].strip().zfill(3)
            # Skip state-level summaries (county FIPS = 000)
            if county_fips == "000":
                continue
            geoid = state_fips + county_fips
            # Use most recent population estimate available
            pop = 0
            for year in ("2024", "2023", "2022"):
                col = f"POPESTIMATE{year}"
                if col in row and row[col].strip():
                    pop = int(row[col].strip())
                    break
            if pop > 0:
                populations[geoid] = pop
    return populations


def run(conn):
    """Load counties into the database."""
    print("=== Loading Counties ===")

    gazetteer = _load_gazetteer()
    print(f"  Parsed {len(gazetteer)} CONUS counties from gazetteer")

    populations = _load_population()
    print(f"  Parsed {len(populations)} county populations")

    with conn.cursor() as cur:
        # Clear existing counties (cascades to dependent tables via ON CONFLICT)
        cur.execute("DELETE FROM dearth_scores")
        cur.execute("DELETE FROM providers")
        cur.execute("DELETE FROM zipcodes")
        cur.execute("DELETE FROM counties")
        conn.commit()

        rows = []
        for fips, county in gazetteer.items():
            pop = populations.get(fips, 0)
            rows.append((
                county["fips"],
                county["name"],
                county["state_fips"],
                county["state_abbr"],
                county["state_name"],
                pop,
                county["land_area_sqmi"],
                f"SRID=4326;POINT({county['lon']} {county['lat']})",
            ))

        print(f"  Inserting {len(rows)} counties...")
        execute_values(
            cur,
            """INSERT INTO counties (fips, name, state_fips, state_abbr, state_name,
               population, land_area_sqmi, centroid)
               VALUES %s ON CONFLICT (fips) DO UPDATE SET
                 name = EXCLUDED.name,
                 population = EXCLUDED.population,
                 land_area_sqmi = EXCLUDED.land_area_sqmi,
                 centroid = EXCLUDED.centroid""",
            rows,
            template="(%s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s))",
        )
        conn.commit()
        print(f"  Inserted {len(rows)} counties")

    print("=== Counties Load Complete ===")


if __name__ == "__main__":
    import psycopg2
    from .config import get_db_params
    conn = psycopg2.connect(**get_db_params())
    try:
        run(conn)
    finally:
        conn.close()

"""Load healthcare providers from the NPPES NPI Registry.

Processes the ~8GB NPPES CSV in chunks of 50,000 rows:
  - Filters to Entity Type 1 (individuals)
  - Matches taxonomy codes to our specialty mapping
  - Geocodes via ZCTA centroid lookup
  - Batch inserts into the `providers` table

Expected output: ~200K-400K providers after specialty filtering.
"""

import csv
import os
import sys

from psycopg2.extras import execute_values

from .config import RAW_DIR
from .download_data import get_nppes_csv_path
from .taxonomy_mapping import SPECIALTY_MAPPING, ALL_TAXONOMY_CODES

# NPPES CSV column indices (0-indexed)
COL_NPI = 0
COL_ENTITY_TYPE = 1
COL_LAST_NAME = 5
COL_FIRST_NAME = 6
COL_PRACTICE_ADDRESS = 28
COL_PRACTICE_CITY = 30
COL_PRACTICE_STATE = 31
COL_PRACTICE_ZIP = 32
# Taxonomy codes are at columns 47, 50, 53, ... (every 3 from 47)
TAXONOMY_COL_START = 47
TAXONOMY_COL_STEP = 4  # Columns: taxonomy, license_num, license_state, primary_switch
TAXONOMY_COL_COUNT = 15  # Up to 15 taxonomy code slots


def _build_zcta_lookup(conn) -> dict[str, tuple[float, float]]:
    """Build ZCTA -> (lat, lon) lookup from the zipcodes table."""
    lookup = {}
    with conn.cursor() as cur:
        cur.execute("""
            SELECT zcta, ST_Y(centroid) AS lat, ST_X(centroid) AS lon
            FROM zipcodes WHERE centroid IS NOT NULL
        """)
        for zcta, lat, lon in cur.fetchall():
            lookup[zcta] = (float(lat), float(lon))
    return lookup


def _extract_taxonomy_codes(row: list[str]) -> list[str]:
    """Extract all non-empty taxonomy codes from an NPPES row."""
    codes = []
    for i in range(TAXONOMY_COL_COUNT):
        idx = TAXONOMY_COL_START + i * TAXONOMY_COL_STEP
        if idx < len(row) and row[idx].strip():
            codes.append(row[idx].strip())
    return codes


def _map_specialties(taxonomy_codes: list[str]) -> list[str]:
    """Map taxonomy codes to specialty codes, returning unique matches."""
    specialties = set()
    for code in taxonomy_codes:
        if code in SPECIALTY_MAPPING:
            specialties.add(SPECIALTY_MAPPING[code])
    return sorted(specialties)


def run(conn):
    """Load providers from NPPES into the database."""
    print("=== Loading Providers from NPPES ===")

    csv_path = get_nppes_csv_path()
    print(f"  NPPES CSV: {csv_path}")
    file_size = os.path.getsize(csv_path)
    print(f"  File size: {file_size / (1024**3):.1f} GB")

    # Build ZCTA lookup
    zcta_lookup = _build_zcta_lookup(conn)
    print(f"  ZCTA centroid lookup: {len(zcta_lookup)} entries")

    with conn.cursor() as cur:
        cur.execute("DELETE FROM providers")
        conn.commit()

    # Process CSV in chunks
    chunk_size = 50_000
    insert_batch_size = 2000
    total_read = 0
    total_matched = 0
    total_geocoded = 0
    total_inserted = 0
    pending_rows = []

    print("  Processing NPPES CSV...")

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header row

        for row in reader:
            total_read += 1

            # Progress every 500K rows
            if total_read % 500_000 == 0:
                sys.stdout.write(
                    f"\r  Processed {total_read:,} rows | "
                    f"Matched: {total_matched:,} | "
                    f"Geocoded: {total_geocoded:,}"
                )
                sys.stdout.flush()

            # Filter: Entity Type 1 = Individual
            if len(row) <= COL_ENTITY_TYPE or row[COL_ENTITY_TYPE].strip() != "1":
                continue

            # Extract taxonomy codes and match to specialties
            taxonomy_codes = _extract_taxonomy_codes(row)
            if not taxonomy_codes:
                continue

            # Check if any taxonomy code matches our mapping
            matched_taxonomies = [c for c in taxonomy_codes if c in ALL_TAXONOMY_CODES]
            if not matched_taxonomies:
                continue

            specialties = _map_specialties(taxonomy_codes)
            if not specialties:
                continue

            total_matched += 1

            # Extract provider info
            npi = row[COL_NPI].strip()
            first_name = row[COL_FIRST_NAME].strip() if COL_FIRST_NAME < len(row) else ""
            last_name = row[COL_LAST_NAME].strip() if COL_LAST_NAME < len(row) else ""
            name = f"{first_name} {last_name}".strip()

            address = row[COL_PRACTICE_ADDRESS].strip()[:200] if COL_PRACTICE_ADDRESS < len(row) else ""
            city = row[COL_PRACTICE_CITY].strip()[:100] if COL_PRACTICE_CITY < len(row) else ""
            state = row[COL_PRACTICE_STATE].strip()[:2] if COL_PRACTICE_STATE < len(row) else ""
            zipcode = row[COL_PRACTICE_ZIP].strip()[:5] if COL_PRACTICE_ZIP < len(row) else ""

            # Geocode via ZCTA centroid
            coords = zcta_lookup.get(zipcode)
            if not coords:
                continue

            total_geocoded += 1
            lat, lon = coords

            pending_rows.append((
                npi, 1, name, address, city, state, zipcode,
                f"SRID=4326;POINT({lon} {lat})",
                matched_taxonomies, specialties, True,
            ))

            # Batch insert
            if len(pending_rows) >= insert_batch_size:
                _insert_batch(conn, pending_rows)
                total_inserted += len(pending_rows)
                pending_rows = []

    # Final batch
    if pending_rows:
        _insert_batch(conn, pending_rows)
        total_inserted += len(pending_rows)

    print()  # newline after progress
    print(f"  Total rows read: {total_read:,}")
    print(f"  Specialty matches: {total_matched:,}")
    print(f"  Geocoded (with ZCTA): {total_geocoded:,}")
    print(f"  Inserted: {total_inserted:,}")
    print("=== Provider Load Complete ===")


def _insert_batch(conn, rows):
    """Insert a batch of provider rows."""
    with conn.cursor() as cur:
        execute_values(
            cur,
            """INSERT INTO providers (npi, entity_type, name, address_line1,
               city, state, zipcode, location, taxonomy_codes, specialties,
               is_active)
               VALUES %s ON CONFLICT (npi) DO UPDATE SET
                 name = EXCLUDED.name,
                 location = EXCLUDED.location,
                 taxonomy_codes = EXCLUDED.taxonomy_codes,
                 specialties = EXCLUDED.specialties""",
            rows,
            template="(%s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s), %s, %s, %s)",
        )
    conn.commit()


if __name__ == "__main__":
    import psycopg2
    from .config import get_db_params
    conn = psycopg2.connect(**get_db_params())
    try:
        run(conn)
    finally:
        conn.close()

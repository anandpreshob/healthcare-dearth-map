"""Load HRSA Health Center Service Delivery and Look-Alike Sites.

Processes the HRSA health center data to identify:
  - Federally Qualified Health Centers (FQHCs) and Look-Alikes
  - Community health center locations serving underserved populations
  - Sites that provide care regardless of ability to pay

Geocodes via ZCTA centroid lookup (same as providers).
"""

import csv
import sys

from psycopg2.extras import execute_values

from .download_data import get_hrsa_health_centers_path


def _find_column(header: list[str], *candidates: str) -> int | None:
    """Find column index by trying multiple candidate names (case-insensitive)."""
    header_lower = [h.lower().strip() for h in header]
    for candidate in candidates:
        if candidate.lower().strip() in header_lower:
            return header_lower.index(candidate.lower().strip())
    return None


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


def run(conn):
    """Load HRSA Health Center data."""
    print("=== Loading HRSA Health Center Sites ===")

    csv_path = get_hrsa_health_centers_path()
    print(f"  CSV: {csv_path}")

    # Build ZCTA lookup for geocoding
    zcta_lookup = _build_zcta_lookup(conn)
    print(f"  ZCTA centroid lookup: {len(zcta_lookup)} entries")

    with conn.cursor() as cur:
        cur.execute("DELETE FROM hrsa_health_centers")
        conn.commit()

    batch = []
    batch_size = 2000
    total_read = 0
    total_geocoded = 0
    total_inserted = 0

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)

        col_type = _find_column(header, "Health Center Type",
                                "health_center_type", "Site Type")
        col_hc_name = _find_column(header, "Health Center Name",
                                   "health_center_name", "Grantee Name")
        col_site_name = _find_column(header, "Site Name", "site_name",
                                     "Site Name / Location")
        col_address = _find_column(header, "Site Address", "site_address",
                                   "Address", "Street Address")
        col_city = _find_column(header, "Site City", "site_city", "City")
        col_state = _find_column(header, "Site State Abbreviation",
                                 "site_state", "State", "State Abbreviation")
        col_zip = _find_column(header, "Site Postal Code", "site_zipcode",
                               "ZIP Code", "Zip Code", "Zip")
        col_phone = _find_column(header, "Site Telephone Number",
                                 "site_phone", "Phone", "Telephone")
        col_web = _find_column(header, "Site Web Address", "site_web_address",
                               "Web Address", "Website")
        col_hours = _find_column(header, "Site Operating Hours",
                                 "operating_hours", "Operating Hours")

        if col_site_name is None and col_hc_name is None:
            print("  ERROR: Could not find site/health center name column.")
            print(f"    Available columns: {header[:20]}")
            return

        print(f"  Site name column: {col_site_name}")
        print(f"  State column: {col_state}")
        print("  Processing rows...")

        def _safe_get(row, idx, maxlen=None):
            if idx is None or idx >= len(row):
                return None
            val = row[idx].strip()
            if not val:
                return None
            if maxlen:
                val = val[:maxlen]
            return val

        for row in reader:
            total_read += 1

            if total_read % 5_000 == 0:
                sys.stdout.write(
                    f"\r  Processed {total_read:,} | Geocoded: {total_geocoded:,}"
                )
                sys.stdout.flush()

            zipcode = _safe_get(row, col_zip, 5)
            state = _safe_get(row, col_state, 2)

            # Skip non-CONUS
            if state and state.upper() in ("AK", "HI", "PR", "GU", "VI", "AS", "MP"):
                continue

            # Geocode via ZCTA
            geom = None
            if zipcode and zipcode in zcta_lookup:
                lat, lon = zcta_lookup[zipcode]
                geom = f"SRID=4326;POINT({lon} {lat})"
                total_geocoded += 1

            batch.append((
                _safe_get(row, col_type, 100),
                _safe_get(row, col_hc_name, 200),
                _safe_get(row, col_site_name, 200),
                _safe_get(row, col_address, 200),
                _safe_get(row, col_city, 100),
                state,
                zipcode,
                _safe_get(row, col_phone, 20),
                _safe_get(row, col_web, 500),
                _safe_get(row, col_hours),
                geom,
            ))

            if len(batch) >= batch_size:
                _insert_batch(conn, batch)
                total_inserted += len(batch)
                batch = []

    if batch:
        _insert_batch(conn, batch)
        total_inserted += len(batch)

    print()
    print(f"  Total rows read: {total_read:,}")
    print(f"  Geocoded: {total_geocoded:,}")
    print(f"  Inserted: {total_inserted:,}")
    print("=== HRSA Health Center Load Complete ===")


def _insert_batch(conn, rows):
    """Insert a batch of health center rows."""
    with conn.cursor() as cur:
        execute_values(
            cur,
            """INSERT INTO hrsa_health_centers (
                health_center_type, health_center_name, site_name,
                site_address, site_city, site_state, site_zipcode,
                site_phone, site_web_address, operating_hours, location
            ) VALUES %s""",
            rows,
            template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s))",
        )
    conn.commit()

"""Load CMS Hospital Timely and Effective Care data.

Processes emergency department wait time measures:
  - OP-18: Median time from ED arrival to ED departure (minutes)
  - OP-20: Median time from ED arrival to admission (minutes)
  - OP-22: Median time from decision to admit to ED departure (minutes)
  - ED-2b: Admit decision time to ED departure for admitted patients

These are hospital-level measures aggregated to county level.
"""

import csv
import sys

from psycopg2.extras import execute_values

from .download_data import get_cms_hospital_timely_care_path

# ED wait time measure IDs we care about
ED_MEASURES = {
    "OP_18",  # Median time from ED arrival to departure (outpatient)
    "OP_18B",
    "OP_20",  # Door to diagnostic eval
    "OP_22",  # Left without being seen
    "ED1",    # ED-1: Median time from ED arrival to departure (admitted)
    "ED2",    # ED-2: Admit decision to ED departure
    "ED_2B",
    "ED1B",
    "ED2B",
    "OP-18",
    "OP-18b",
    "OP-20",
    "OP-22",
    "ED-1",
    "ED-1b",
    "ED-2b",
}


def _find_column(header: list[str], *candidates: str) -> int | None:
    """Find column index by trying multiple candidate names (case-insensitive)."""
    header_lower = [h.lower().strip() for h in header]
    for candidate in candidates:
        if candidate.lower().strip() in header_lower:
            return header_lower.index(candidate.lower().strip())
    return None


def _parse_int(val: str) -> int | None:
    """Parse integer, returning None for empty/invalid."""
    if not val or not val.strip():
        return None
    try:
        return int(val.strip().replace(",", ""))
    except ValueError:
        return None


def run(conn):
    """Load CMS Hospital Timely and Effective Care data."""
    print("=== Loading CMS Hospital Timely & Effective Care ===")

    csv_path = get_cms_hospital_timely_care_path()
    print(f"  CSV: {csv_path}")

    with conn.cursor() as cur:
        cur.execute("DELETE FROM cms_hospital_timely_care")
        conn.commit()

    batch = []
    batch_size = 5000
    total_read = 0
    total_ed = 0
    total_inserted = 0

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)

        col_facility_id = _find_column(header, "Facility ID", "facility_id",
                                       "Provider ID", "provider_id", "CMS Certification Number")
        col_facility_name = _find_column(header, "Facility Name", "facility_name",
                                         "Hospital Name", "hospital_name")
        col_city = _find_column(header, "City/Town", "City", "city")
        col_state = _find_column(header, "State", "state", "st")
        col_zip = _find_column(header, "ZIP Code", "Zip Code", "zip", "zipcode")
        col_county = _find_column(header, "County/Parish", "County Name",
                                  "county_name", "County")
        col_measure_id = _find_column(header, "Measure ID", "measure_id",
                                      "HCAHPS Measure ID")
        col_measure_name = _find_column(header, "Measure Name", "measure_name",
                                         "HCAHPS Question")
        col_score = _find_column(header, "Score", "score", "Rate",
                                 "HCAHPS Answer Percent")
        col_sample = _find_column(header, "Sample", "sample",
                                  "Number of Completed Surveys",
                                  "Denominator")
        col_start = _find_column(header, "Start Date", "start_date",
                                 "Measure Start Date")
        col_end = _find_column(header, "End Date", "end_date",
                               "Measure End Date")

        if col_facility_id is None:
            print("  ERROR: Could not find Facility ID column. Available columns:")
            print(f"    {header[:20]}")
            return

        if col_measure_id is None:
            print("  ERROR: Could not find Measure ID column. Available columns:")
            print(f"    {header[:20]}")
            return

        print(f"  Facility ID column: {col_facility_id}")
        print(f"  Measure ID column: {col_measure_id}")
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

        # Normalize measure ID variants
        ed_measures_normalized = {m.upper().replace("-", "_").replace(" ", "_")
                                  for m in ED_MEASURES}

        for row in reader:
            total_read += 1

            if total_read % 100_000 == 0:
                sys.stdout.write(f"\r  Processed {total_read:,} | ED measures: {total_ed:,}")
                sys.stdout.flush()

            measure_id = _safe_get(row, col_measure_id)
            if not measure_id:
                continue

            # Normalize for comparison
            measure_normalized = measure_id.upper().replace("-", "_").replace(" ", "_")

            # Keep all measures (not just ED) so we have comprehensive hospital data
            # but flag ED measures specially
            is_ed = measure_normalized in ed_measures_normalized
            if is_ed:
                total_ed += 1

            facility_id = _safe_get(row, col_facility_id, 10)
            if not facility_id:
                continue

            batch.append((
                facility_id,
                _safe_get(row, col_facility_name, 200),
                _safe_get(row, col_city, 100),
                _safe_get(row, col_state, 2),
                _safe_get(row, col_zip, 10),
                _safe_get(row, col_county, 100),
                measure_id[:30],
                _safe_get(row, col_measure_name, 300),
                _safe_get(row, col_score, 20),
                _parse_int(_safe_get(row, col_sample) or ""),
                _safe_get(row, col_start, 20),
                _safe_get(row, col_end, 20),
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
    print(f"  ED-related measures: {total_ed:,}")
    print(f"  Inserted: {total_inserted:,}")
    print("=== Hospital Timely Care Load Complete ===")


def _insert_batch(conn, rows):
    """Insert a batch of hospital timely care rows."""
    with conn.cursor() as cur:
        execute_values(
            cur,
            """INSERT INTO cms_hospital_timely_care (
                facility_id, facility_name, city, state, zipcode,
                county_name, measure_id, measure_name, score, sample,
                start_date, end_date
            ) VALUES %s
            ON CONFLICT (facility_id, measure_id) DO UPDATE SET
                score = EXCLUDED.score,
                sample = EXCLUDED.sample,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date""",
            rows,
        )
    conn.commit()

"""Load CMS Care Compare (DAC) data to enrich providers with Medicare participation.

Processes the CMS Doctors and Clinicians National Downloadable File:
  - Medicare assignment acceptance (Y/N)
  - EHR participation
  - Quality measure reporting
  - Organization/group practice info

Joins to existing providers table via NPI for enrichment.
"""

import csv
import sys

from psycopg2.extras import execute_values

from .download_data import get_cms_care_compare_path


# Column names from the DAC National Downloadable File
# The file uses header names; we map the ones we care about
FIELD_MAP = {
    "npi": "NPI",
    "pac_id": "Ind_PAC_ID",
    "last_name": "lst_nm",
    "first_name": "frst_nm",
    "credential": "Cred",
    "medical_school": "Med_sch",
    "graduation_year": "Grd_yr",
    "primary_specialty": "pri_spec",
    "organization_legal_name": "org_nm",
    "org_pac_id": "org_pac_id",
    "num_org_members": "num_org_mem",
    "city": "cty",
    "state": "st",
    "zipcode": "zip",
    "phone_number": "phn_numbr",
    "accepts_medicare_assignment": "assgn",
    "participates_in_ehr": "ind_enrl_ID",  # fallback field
    "reported_quality_measures": "Participating in eRx",  # fallback field
}


def _parse_bool(val: str) -> bool | None:
    """Parse Y/N/M values to boolean."""
    if not val or not val.strip():
        return None
    v = val.strip().upper()
    if v in ("Y", "YES", "TRUE", "1"):
        return True
    if v in ("N", "NO", "FALSE", "0"):
        return False
    return None


def _parse_int(val: str) -> int | None:
    """Parse integer, returning None for empty/invalid."""
    if not val or not val.strip():
        return None
    try:
        return int(val.strip())
    except ValueError:
        return None


def _find_column(header: list[str], *candidates: str) -> int | None:
    """Find column index by trying multiple candidate names (case-insensitive)."""
    header_lower = [h.lower().strip() for h in header]
    for candidate in candidates:
        candidate_lower = candidate.lower().strip()
        if candidate_lower in header_lower:
            return header_lower.index(candidate_lower)
    return None


def run(conn):
    """Load CMS Care Compare data into the database."""
    print("=== Loading CMS Care Compare Data ===")

    csv_path = get_cms_care_compare_path()
    print(f"  CSV: {csv_path}")

    with conn.cursor() as cur:
        cur.execute("DELETE FROM cms_care_compare")
        conn.commit()

    batch = []
    batch_size = 5000
    total_read = 0
    total_inserted = 0

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)

        # Find column indices dynamically
        col_npi = _find_column(header, "NPI", "npi")
        col_pac = _find_column(header, "Ind_PAC_ID", "ind_pac_id", "PAC ID")
        col_last = _find_column(header, "lst_nm", "last_name", "Last Name")
        col_first = _find_column(header, "frst_nm", "first_name", "First Name")
        col_cred = _find_column(header, "Cred", "credential", "Credential")
        col_med_sch = _find_column(header, "Med_sch", "medical_school", "Medical school name")
        col_grad_yr = _find_column(header, "Grd_yr", "graduation_year", "Graduation year")
        col_spec = _find_column(header, "pri_spec", "primary_specialty", "Primary specialty")
        col_org_name = _find_column(header, "org_nm", "Organization legal name")
        col_org_pac = _find_column(header, "org_pac_id", "Organization PAC ID")
        col_num_org = _find_column(header, "num_org_mem", "Number of Group Practice members")
        col_city = _find_column(header, "cty", "City/Town")
        col_state = _find_column(header, "st", "State")
        col_zip = _find_column(header, "zip", "Zip Code")
        col_phone = _find_column(header, "phn_numbr", "Phone Number")
        col_assgn = _find_column(header, "assgn", "Accepts Medicare Assignment",
                                 "Medicare Assignment", "Accepts Medicare")
        col_ehr = _find_column(header, "Clinician made meaningful use",
                               "Uses electronic health records", "ehr")
        col_quality = _find_column(header, "Reported Quality Measures",
                                   "reported_quality_measures", "Quality")

        if col_npi is None:
            print("  ERROR: Could not find NPI column. Available columns:")
            print(f"    {header[:20]}")
            return

        print(f"  Found NPI column at index {col_npi}")
        print(f"  Medicare assignment column: {col_assgn}")
        print(f"  Processing rows...")

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

            if total_read % 500_000 == 0:
                sys.stdout.write(f"\r  Processed {total_read:,} rows | Inserted: {total_inserted:,}")
                sys.stdout.flush()

            npi = _safe_get(row, col_npi, 10)
            if not npi:
                continue

            batch.append((
                npi,
                _safe_get(row, col_pac, 10),
                _safe_get(row, col_last, 100),
                _safe_get(row, col_first, 100),
                _safe_get(row, col_cred, 20),
                _safe_get(row, col_med_sch, 200),
                _parse_int(_safe_get(row, col_grad_yr) or ""),
                _safe_get(row, col_spec, 200),
                _safe_get(row, col_org_name, 200),
                _safe_get(row, col_org_pac, 10),
                _parse_int(_safe_get(row, col_num_org) or ""),
                _safe_get(row, col_city, 100),
                _safe_get(row, col_state, 2),
                _safe_get(row, col_zip, 10),
                _safe_get(row, col_phone, 20),
                _parse_bool(_safe_get(row, col_assgn) or ""),
                _parse_bool(_safe_get(row, col_ehr) or ""),
                _parse_bool(_safe_get(row, col_quality) or ""),
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
    print(f"  Inserted: {total_inserted:,}")

    # Print summary stats
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM cms_care_compare")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM cms_care_compare WHERE accepts_medicare_assignment = TRUE")
        medicare_yes = cur.fetchone()[0]
        print(f"  Total records: {total:,}")
        print(f"  Accepts Medicare assignment: {medicare_yes:,} ({100*medicare_yes/max(total,1):.1f}%)")

    print("=== CMS Care Compare Load Complete ===")


def _insert_batch(conn, rows):
    """Insert a batch of CMS Care Compare rows."""
    with conn.cursor() as cur:
        execute_values(
            cur,
            """INSERT INTO cms_care_compare (
                npi, pac_id, last_name, first_name, credential,
                medical_school, graduation_year, primary_specialty,
                organization_legal_name, org_pac_id, num_org_members,
                city, state, zipcode, phone_number,
                accepts_medicare_assignment, participates_in_ehr,
                reported_quality_measures
            ) VALUES %s
            ON CONFLICT (npi) DO UPDATE SET
                accepts_medicare_assignment = EXCLUDED.accepts_medicare_assignment,
                participates_in_ehr = EXCLUDED.participates_in_ehr,
                reported_quality_measures = EXCLUDED.reported_quality_measures,
                organization_legal_name = EXCLUDED.organization_legal_name,
                primary_specialty = EXCLUDED.primary_specialty""",
            rows,
        )
    conn.commit()

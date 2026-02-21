"""Compute actual drive times via OSRM road-network routing.

Queries the OSRM routing engine for each (county centroid -> nearest provider)
pair. Falls back to a distance-based proxy when OSRM is unavailable.

Runs between compute_metrics (which stores nearest provider coords) and
compute_scores (which uses drive_time_minutes for percentile scoring).
"""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from .config import OSRM_URL, DRIVETIME_PROXY_FACTOR


def _check_osrm(session: requests.Session) -> bool:
    """Check if OSRM is reachable with a test route."""
    try:
        resp = session.get(
            f"{OSRM_URL}/route/v1/driving/-73.98,40.74;-73.97,40.75",
            params={"overview": "false"},
            timeout=5,
        )
        return resp.status_code == 200 and resp.json().get("code") == "Ok"
    except (requests.ConnectionError, requests.Timeout, ValueError):
        return False


def _route_one(session: requests.Session, row: tuple) -> tuple:
    """Query OSRM for a single county->provider route.

    Args:
        session: reusable requests session
        row: (id, county_lon, county_lat, provider_lon, provider_lat, distance_miles)

    Returns:
        (id, drive_time_minutes, is_estimated)
    """
    row_id, c_lon, c_lat, p_lon, p_lat, dist_miles = row

    try:
        resp = session.get(
            f"{OSRM_URL}/route/v1/driving/{c_lon},{c_lat};{p_lon},{p_lat}",
            params={"overview": "false"},
            timeout=10,
        )
        data = resp.json()

        if data.get("code") == "Ok" and data.get("routes"):
            duration_sec = data["routes"][0]["duration"]
            drive_minutes = duration_sec / 60.0
            return (row_id, drive_minutes, False)

    except (requests.ConnectionError, requests.Timeout, ValueError, KeyError,
            IndexError):
        pass

    # Fallback: proxy estimate
    return (row_id, dist_miles * DRIVETIME_PROXY_FACTOR, True)


def run(conn):
    """Compute drive times for all county-specialty pairs via OSRM."""
    print("=== Computing Drive Times (OSRM) ===")

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=25,
        pool_maxsize=25,
        max_retries=1,
    )
    session.mount("http://", adapter)

    # Check OSRM availability
    if not _check_osrm(session):
        print("  WARNING: OSRM not reachable. Keeping proxy drive times.")
        print("  To enable OSRM: docker compose up osrm")
        return

    print(f"  OSRM connected at {OSRM_URL}")

    with conn.cursor() as cur:
        # Get specialties
        cur.execute("SELECT code FROM specialties ORDER BY code")
        specialty_codes = [row[0] for row in cur.fetchall()]

        total_routed = 0
        total_estimated = 0

        for i, spec in enumerate(specialty_codes, 1):
            sys.stdout.write(f"\r  [{i}/{len(specialty_codes)}] {spec:<20}")
            sys.stdout.flush()

            # Fetch rows that have nearest provider coords
            cur.execute("""
                SELECT
                    ds.id,
                    ST_X(c.centroid) AS county_lon,
                    ST_Y(c.centroid) AS county_lat,
                    ds.nearest_provider_lon,
                    ds.nearest_provider_lat,
                    ds.nearest_distance_miles
                FROM dearth_scores ds
                JOIN counties c ON c.fips = ds.geo_id
                WHERE ds.geo_type = 'county'
                  AND ds.specialty_code = %s
                  AND ds.nearest_provider_lon IS NOT NULL
                  AND ds.nearest_provider_lat IS NOT NULL
            """, (spec,))
            rows = cur.fetchall()

            if not rows:
                continue

            # Query OSRM in parallel
            results = []
            with ThreadPoolExecutor(max_workers=25) as pool:
                futures = {
                    pool.submit(_route_one, session, row): row
                    for row in rows
                }
                for future in as_completed(futures):
                    results.append(future.result())

            # Batch update
            routed = sum(1 for _, _, est in results if not est)
            estimated = sum(1 for _, _, est in results if est)
            total_routed += routed
            total_estimated += estimated

            # Use executemany for batch update
            cur.executemany(
                """UPDATE dearth_scores
                   SET drive_time_minutes = %s,
                       drive_time_is_estimated = %s
                   WHERE id = %s""",
                [(dt, est, rid) for rid, dt, est in results],
            )
            conn.commit()

        print()  # newline after progress
        print(f"  Routed: {total_routed:,} | Estimated (fallback): {total_estimated:,}")

    print("=== Drive Time Computation Complete ===")

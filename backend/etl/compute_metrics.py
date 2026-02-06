"""Compute provider metrics per (county, specialty) pair.

Two-phase approach optimized for ~3,143 counties x 15 specialties:

Phase 1 (fast, no spatial): Provider counts and density via zipcode joins.
Phase 2 (spatial, per-specialty): Nearest-provider distance using PostGIS KNN.
"""

import sys


def run(conn):
    """Compute metrics and insert into dearth_scores."""
    print("=== Computing Provider Metrics ===")

    with conn.cursor() as cur:
        # Clear previous metric data
        cur.execute("DELETE FROM dearth_scores")
        conn.commit()

        # -------------------------------------------------------
        # Phase 1: Provider counts and density (no spatial query)
        # -------------------------------------------------------
        print("  Phase 1: Computing provider counts and density...")
        cur.execute("""
            INSERT INTO dearth_scores (
                geo_type, geo_id, specialty_code,
                provider_count, provider_density,
                nearest_distance_miles, avg_distance_top3_miles,
                drive_time_minutes, wait_time_days,
                data_version
            )
            SELECT
                'county' AS geo_type,
                c.fips AS geo_id,
                s.code AS specialty_code,
                COALESCE(cnt.n, 0) AS provider_count,
                CASE
                    WHEN c.population > 0
                    THEN COALESCE(cnt.n, 0) * 100000.0 / c.population
                    ELSE 0
                END AS provider_density,
                999.0 AS nearest_distance_miles,
                999.0 AS avg_distance_top3_miles,
                999.0 AS drive_time_minutes,
                14.0 AS wait_time_days,
                'nppes_v1' AS data_version
            FROM counties c
            CROSS JOIN specialties s
            LEFT JOIN (
                SELECT z.county_fips, spec.val AS specialty,
                       COUNT(DISTINCT p.npi) AS n
                FROM providers p
                JOIN zipcodes z ON z.zcta = p.zipcode
                CROSS JOIN LATERAL unnest(p.specialties) AS spec(val)
                WHERE p.is_active = TRUE
                GROUP BY z.county_fips, spec.val
            ) cnt ON cnt.county_fips = c.fips AND cnt.specialty = s.code
            ON CONFLICT (geo_type, geo_id, specialty_code) DO UPDATE SET
                provider_count = EXCLUDED.provider_count,
                provider_density = EXCLUDED.provider_density,
                computed_at = NOW(),
                data_version = EXCLUDED.data_version;
        """)
        rows = cur.rowcount
        conn.commit()
        print(f"  Phase 1 complete: {rows:,} metric rows")

        # -------------------------------------------------------
        # Phase 2: Distance metrics per specialty using PostGIS KNN
        # -------------------------------------------------------
        print("  Phase 2: Computing distance metrics per specialty...")

        # Get list of specialties
        cur.execute("SELECT code FROM specialties ORDER BY code")
        specialty_codes = [row[0] for row in cur.fetchall()]

        for i, spec in enumerate(specialty_codes, 1):
            sys.stdout.write(f"\r  [{i}/{len(specialty_codes)}] {spec:<20}")
            sys.stdout.flush()

            # Count providers with this specialty
            cur.execute(
                "SELECT COUNT(*) FROM providers WHERE %s = ANY(specialties) AND is_active",
                (spec,),
            )
            provider_count = cur.fetchone()[0]

            if provider_count == 0:
                # No providers for this specialty: leave distances at 999
                continue

            # Update nearest distance and avg top-3 distance for all counties
            # Uses PostGIS KNN operator (<->) with GIST index for fast lookups
            cur.execute("""
                UPDATE dearth_scores ds SET
                    nearest_distance_miles = sub.nearest_miles,
                    avg_distance_top3_miles = sub.avg_top3_miles,
                    drive_time_minutes = sub.nearest_miles * 1.5
                FROM (
                    SELECT c.fips,
                        nearest.d_miles AS nearest_miles,
                        top3.avg_miles AS avg_top3_miles
                    FROM counties c
                    LEFT JOIN LATERAL (
                        SELECT ST_Distance(
                            c.centroid::geography,
                            p.location::geography
                        ) / 1609.34 AS d_miles
                        FROM providers p
                        WHERE %(spec)s = ANY(p.specialties)
                          AND p.is_active = TRUE
                        ORDER BY c.centroid <-> p.location
                        LIMIT 1
                    ) nearest ON TRUE
                    LEFT JOIN LATERAL (
                        SELECT AVG(
                            ST_Distance(
                                c.centroid::geography,
                                p.location::geography
                            ) / 1609.34
                        ) AS avg_miles
                        FROM (
                            SELECT location
                            FROM providers p
                            WHERE %(spec)s = ANY(p.specialties)
                              AND p.is_active = TRUE
                            ORDER BY c.centroid <-> p.location
                            LIMIT 3
                        ) AS p
                    ) top3 ON TRUE
                ) sub
                WHERE ds.geo_type = 'county'
                  AND ds.geo_id = sub.fips
                  AND ds.specialty_code = %(spec)s;
            """, {"spec": spec})
            conn.commit()

        print()  # newline after progress
        print("  Phase 2 complete")

    print("=== Metrics Computation Complete ===")

"""Compute provider metrics per (county, specialty) pair.

For each combination:
- Count providers
- Calculate density per 100k population
- Calculate nearest provider distance from county centroid (miles)
- Calculate average distance to nearest 3 providers (miles)
"""

import psycopg2


def run(conn):
    """Compute metrics and insert into dearth_scores."""
    print("=== Computing Provider Metrics ===")

    with conn.cursor() as cur:
        # Clear previous metric data
        cur.execute("DELETE FROM dearth_scores")
        conn.commit()

        # For each (county, specialty), compute metrics using PostGIS
        # Providers are linked to counties via zipcodes.county_fips
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
                COALESCE(local_cnt.cnt, 0) AS provider_count,
                CASE
                    WHEN c.population > 0
                    THEN COALESCE(local_cnt.cnt, 0) * 100000.0 / c.population
                    ELSE 0
                END AS provider_density,
                COALESCE(nearest.nearest_miles, 999.0) AS nearest_distance_miles,
                COALESCE(nearest.avg_top3_miles, 999.0) AS avg_distance_top3_miles,
                COALESCE(nearest.nearest_miles * 1.5, 999.0) AS drive_time_minutes,
                14.0 AS wait_time_days,
                'sample_v1' AS data_version
            FROM counties c
            CROSS JOIN specialties s
            -- Count providers in THIS county (via zipcode -> county_fips)
            LEFT JOIN LATERAL (
                SELECT COUNT(*) AS cnt
                FROM providers p
                JOIN zipcodes z ON z.zcta = p.zipcode
                WHERE z.county_fips = c.fips
                  AND s.code = ANY(p.specialties)
                  AND p.is_active = TRUE
            ) local_cnt ON TRUE
            -- Distance metrics: nearest provider of this specialty anywhere
            LEFT JOIN LATERAL (
                SELECT
                    MIN(
                        ST_Distance(c.centroid::geography, p.location::geography) / 1609.34
                    ) AS nearest_miles,
                    (
                        SELECT AVG(d_miles) FROM (
                            SELECT
                                ST_Distance(c.centroid::geography, p2.location::geography) / 1609.34 AS d_miles
                            FROM providers p2
                            WHERE s.code = ANY(p2.specialties)
                              AND p2.is_active = TRUE
                            ORDER BY ST_Distance(c.centroid::geography, p2.location::geography)
                            LIMIT 3
                        ) AS top3
                    ) AS avg_top3_miles
                FROM providers p
                WHERE s.code = ANY(p.specialties)
                  AND p.is_active = TRUE
            ) nearest ON TRUE
            ON CONFLICT (geo_type, geo_id, specialty_code) DO UPDATE SET
                provider_count = EXCLUDED.provider_count,
                provider_density = EXCLUDED.provider_density,
                nearest_distance_miles = EXCLUDED.nearest_distance_miles,
                avg_distance_top3_miles = EXCLUDED.avg_distance_top3_miles,
                drive_time_minutes = EXCLUDED.drive_time_minutes,
                wait_time_days = EXCLUDED.wait_time_days,
                computed_at = NOW(),
                data_version = EXCLUDED.data_version;
        """)
        rows = cur.rowcount
        conn.commit()
        print(f"  Inserted/updated {rows} metric rows")

    print("=== Metrics Computation Complete ===")

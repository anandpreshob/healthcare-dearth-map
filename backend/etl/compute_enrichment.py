"""Compute county-level enrichment metrics from CMS and HRSA data.

Aggregates the following to county_enrichment table:
  1. CMS Care Compare: % accepting Medicare, % EHR, % quality reporting
  2. CMS Hospital: Median ED wait times per county
  3. HRSA Health Centers: Count of health center sites per county
"""


def run(conn):
    """Aggregate enrichment data at county level."""
    print("=== Computing County Enrichment Metrics ===")

    with conn.cursor() as cur:
        # Clear existing enrichment data
        cur.execute("DELETE FROM county_enrichment")
        conn.commit()

        # Initialize all counties with defaults
        cur.execute("""
            INSERT INTO county_enrichment (fips)
            SELECT fips FROM counties
        """)
        conn.commit()
        print(f"  Initialized {cur.rowcount} counties")

        # ----------------------------------------------------------
        # 1. CMS Care Compare: Medicare participation aggregates
        # ----------------------------------------------------------
        print("  Aggregating CMS Care Compare by county...")
        cur.execute("""
            UPDATE county_enrichment ce SET
                total_medicare_providers = sub.total,
                pct_accepting_medicare = sub.pct_medicare,
                pct_ehr_participation = sub.pct_ehr,
                pct_quality_reporting = sub.pct_quality
            FROM (
                SELECT
                    z.county_fips AS fips,
                    COUNT(*) AS total,
                    100.0 * COUNT(*) FILTER (
                        WHERE cc.accepts_medicare_assignment = TRUE
                    ) / GREATEST(COUNT(*), 1) AS pct_medicare,
                    100.0 * COUNT(*) FILTER (
                        WHERE cc.participates_in_ehr = TRUE
                    ) / GREATEST(COUNT(*), 1) AS pct_ehr,
                    100.0 * COUNT(*) FILTER (
                        WHERE cc.reported_quality_measures = TRUE
                    ) / GREATEST(COUNT(*), 1) AS pct_quality
                FROM cms_care_compare cc
                JOIN zipcodes z ON z.zcta = LEFT(cc.zipcode, 5)
                WHERE cc.state IS NOT NULL
                GROUP BY z.county_fips
            ) sub
            WHERE ce.fips = sub.fips
        """)
        conn.commit()
        print(f"  Updated {cur.rowcount} counties with Medicare data")

        # ----------------------------------------------------------
        # 2. CMS Hospital Timely Care: ED wait times
        # ----------------------------------------------------------
        print("  Aggregating hospital ED wait times by county...")

        # OP-18 is "Median Time Patients Spent in the Emergency Department"
        # We try to parse the score as an integer (minutes)
        cur.execute("""
            UPDATE county_enrichment ce SET
                median_ed_wait_minutes = sub.median_score,
                avg_ed_wait_minutes = sub.avg_score,
                num_hospitals_reporting = sub.num_hospitals
            FROM (
                SELECT
                    z.county_fips AS fips,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (
                        ORDER BY score_val
                    ) AS median_score,
                    AVG(score_val) AS avg_score,
                    COUNT(DISTINCT h.facility_id) AS num_hospitals
                FROM cms_hospital_timely_care h
                JOIN zipcodes z ON z.zcta = LEFT(h.zipcode, 5)
                CROSS JOIN LATERAL (
                    SELECT CAST(
                        NULLIF(REGEXP_REPLACE(h.score, '[^0-9.]', '', 'g'), '')
                        AS FLOAT
                    ) AS score_val
                ) parsed
                WHERE h.measure_id IN (
                    'OP_18', 'OP-18', 'OP_18b', 'OP-18b',
                    'ED1', 'ED-1', 'ED1b', 'ED-1b'
                )
                AND parsed.score_val IS NOT NULL
                AND parsed.score_val > 0
                AND parsed.score_val < 1440
                GROUP BY z.county_fips
            ) sub
            WHERE ce.fips = sub.fips
        """)
        conn.commit()
        print(f"  Updated {cur.rowcount} counties with ED wait time data")

        # ----------------------------------------------------------
        # 3. HRSA Health Centers: Site counts per county
        # ----------------------------------------------------------
        print("  Aggregating HRSA health center sites by county...")
        cur.execute("""
            UPDATE county_enrichment ce SET
                health_center_sites = sub.site_count,
                health_center_sites_per_100k = CASE
                    WHEN c.population > 0
                    THEN sub.site_count * 100000.0 / c.population
                    ELSE 0
                END
            FROM (
                SELECT
                    z.county_fips AS fips,
                    COUNT(*) AS site_count
                FROM hrsa_health_centers hc
                JOIN zipcodes z ON z.zcta = LEFT(hc.site_zipcode, 5)
                WHERE hc.site_state IS NOT NULL
                GROUP BY z.county_fips
            ) sub
            JOIN counties c ON c.fips = sub.fips
            WHERE ce.fips = sub.fips
        """)
        conn.commit()
        print(f"  Updated {cur.rowcount} counties with health center data")

        # ----------------------------------------------------------
        # Summary statistics
        # ----------------------------------------------------------
        cur.execute("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE total_medicare_providers > 0) AS has_medicare,
                COUNT(*) FILTER (WHERE median_ed_wait_minutes IS NOT NULL) AS has_ed_wait,
                COUNT(*) FILTER (WHERE health_center_sites > 0) AS has_hc,
                ROUND(AVG(pct_accepting_medicare)::numeric, 1) AS avg_pct_medicare,
                ROUND(AVG(median_ed_wait_minutes)::numeric, 1) AS avg_ed_wait,
                SUM(health_center_sites) AS total_hc_sites
            FROM county_enrichment
        """)
        row = cur.fetchone()
        print(f"  Summary:")
        print(f"    Counties with Medicare data: {row[1]}/{row[0]}")
        print(f"    Counties with ED wait data: {row[2]}/{row[0]}")
        print(f"    Counties with health centers: {row[3]}/{row[0]}")
        print(f"    Avg % accepting Medicare: {row[4]}%")
        print(f"    Avg median ED wait: {row[5]} min")
        print(f"    Total health center sites: {row[6]}")

    print("=== County Enrichment Complete ===")

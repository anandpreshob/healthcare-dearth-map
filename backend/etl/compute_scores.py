"""Compute dearth scores from provider metrics.

Scoring methodology:
- density_score = 100 * (1 - percentile_rank(density))
- drivetime_score = 100 * percentile_rank(drive_time_minutes)
- dearth_score = 0.6*density + 0.4*drivetime

Labels:
  0-20  Well Served
  21-40 Adequate
  41-60 Moderate Shortage
  61-80 Significant Shortage
  81-100 Severe Shortage
"""

from .config import (
    WEIGHT_DENSITY,
    WEIGHT_DRIVETIME,
    DEARTH_LABELS,
)


def run(conn):
    """Compute dearth scores using percentile ranks within each specialty."""
    print("=== Computing Dearth Scores ===")

    with conn.cursor() as cur:
        # Step 1: Compute percentile-based component scores
        print("  Computing component scores (percentile ranks)...")
        cur.execute("""
            UPDATE dearth_scores ds SET
                density_score = sub.density_score,
                drivetime_score = sub.drivetime_score,
                computed_at = NOW()
            FROM (
                SELECT
                    id,
                    100.0 * (1.0 - PERCENT_RANK() OVER (
                        PARTITION BY specialty_code
                        ORDER BY provider_density
                    )) AS density_score,
                    100.0 * PERCENT_RANK() OVER (
                        PARTITION BY specialty_code
                        ORDER BY drive_time_minutes
                    ) AS drivetime_score
                FROM dearth_scores
            ) sub
            WHERE ds.id = sub.id;
        """)
        conn.commit()
        print(f"  Updated {cur.rowcount} component scores")

        # Step 2: Compute composite dearth_score
        print("  Computing composite dearth scores...")
        cur.execute("""
            UPDATE dearth_scores SET
                dearth_score = LEAST(100.0, GREATEST(0.0,
                    %(w_density)s * COALESCE(density_score, 50) +
                    %(w_drivetime)s * COALESCE(drivetime_score, 50)
                )),
                computed_at = NOW();
        """, {
            "w_density": WEIGHT_DENSITY,
            "w_drivetime": WEIGHT_DRIVETIME,
        })
        conn.commit()
        print(f"  Updated {cur.rowcount} composite scores")

        # Step 3: Assign labels based on score ranges
        print("  Assigning dearth labels...")
        for threshold, label in DEARTH_LABELS:
            if label == DEARTH_LABELS[0][1]:
                cur.execute(
                    "UPDATE dearth_scores SET dearth_label = %s WHERE dearth_score <= %s",
                    (label, threshold),
                )
            else:
                prev_threshold = 0
                for t, l in DEARTH_LABELS:
                    if l == label:
                        break
                    prev_threshold = t
                cur.execute(
                    "UPDATE dearth_scores SET dearth_label = %s WHERE dearth_score > %s AND dearth_score <= %s",
                    (label, prev_threshold, threshold),
                )
        conn.commit()

        # Step 4: Refresh materialized view
        print("  Refreshing materialized view county_dearth_summary...")
        cur.execute("REFRESH MATERIALIZED VIEW county_dearth_summary;")
        conn.commit()

        # Print summary stats
        cur.execute("""
            SELECT dearth_label, COUNT(*)
            FROM dearth_scores
            GROUP BY dearth_label
            ORDER BY MIN(dearth_score);
        """)
        print("  Score distribution:")
        for row in cur.fetchall():
            print(f"    {row[0]}: {row[1]}")

    print("=== Dearth Score Computation Complete ===")

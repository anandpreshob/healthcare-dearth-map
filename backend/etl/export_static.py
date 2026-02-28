"""
Export all API data as static JSON files for GitHub Pages deployment.

Usage:
    python -m backend.etl.export_static
    python -m backend.etl.export_static --output-dir ./docs/data
"""

import argparse
import csv
import io
import json
import os

import psycopg2

from .config import get_db_params

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "frontend", "public", "data"
)


def _round(val, decimals=2):
    """Round a numeric value, returning None for None."""
    if val is None:
        return None
    return round(float(val), decimals)


def _compact_json(obj):
    """Serialize to compact JSON (no whitespace)."""
    return json.dumps(obj, separators=(",", ":"))


def export_specialties(cur, out):
    """Export specialties.json."""
    cur.execute("SELECT code, name FROM specialties ORDER BY name")
    rows = [{"code": r[0], "name": r[1]} for r in cur.fetchall()]
    path = os.path.join(out, "specialties.json")
    with open(path, "w") as f:
        f.write(_compact_json(rows))
    print(f"  specialties.json ({len(rows)} specialties)")
    return [r["code"] for r in rows]


def export_geojson(cur, out, specialty_codes):
    """Export GeoJSON FeatureCollection files (one per specialty)."""
    for code in specialty_codes:
        cur.execute(
            """
            SELECT fips, name, state_abbr, population,
                   dearth_score, dearth_label, provider_count, provider_density
            FROM county_dearth_summary
            WHERE specialty = %s
            ORDER BY fips
            """,
            (code,),
        )
        features = []
        for r in cur.fetchall():
            fips, name, state, pop, score, label, pcount, pdensity = r
            features.append(
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {
                        "fips": fips,
                        "name": name,
                        "state": state,
                        "population": pop,
                        "dearth_score": _round(score) if score is not None else 0,
                        "dearth_label": label or "N/A",
                        "provider_count": pcount,
                        "provider_density": (
                            _round(pdensity) if pdensity is not None else 0
                        ),
                    },
                }
            )
        collection = {"type": "FeatureCollection", "features": features}
        path = os.path.join(out, "geojson", f"counties_{code}.json")
        with open(path, "w") as f:
            f.write(_compact_json(collection))
        print(f"  geojson/counties_{code}.json ({len(features)} features)")


def export_counties(cur, out, specialty_codes):
    """Export county list files (one per specialty, for table view)."""
    for code in specialty_codes:
        cur.execute(
            """
            SELECT fips, name, state_abbr, population,
                   dearth_score, dearth_label, provider_count, provider_density
            FROM county_dearth_summary
            WHERE specialty = %s
            ORDER BY dearth_score DESC NULLS LAST
            """,
            (code,),
        )
        rows = []
        for r in cur.fetchall():
            fips, name, state, pop, score, label, pcount, pdensity = r
            rows.append(
                {
                    "fips": fips,
                    "name": name,
                    "state": state,
                    "population": pop,
                    "dearth_score": _round(score),
                    "dearth_label": label,
                    "provider_count": pcount,
                    "provider_density": _round(pdensity),
                }
            )
        path = os.path.join(out, "counties", f"counties_{code}.json")
        with open(path, "w") as f:
            f.write(_compact_json(rows))
        print(f"  counties/counties_{code}.json ({len(rows)} rows)")


def export_details(cur, out):
    """Export bundled county detail file with all specialties."""
    # Pre-compute state averages
    cur.execute(
        """
        SELECT ds.specialty_code, c.state_abbr, AVG(ds.dearth_score)
        FROM dearth_scores ds
        JOIN counties c ON c.fips = ds.geo_id AND ds.geo_type = 'county'
        GROUP BY ds.specialty_code, c.state_abbr
        """
    )
    state_avgs = {}
    for code, state, avg in cur.fetchall():
        state_avgs[(code, state)] = _round(avg)

    # Pre-compute national averages
    cur.execute(
        """
        SELECT specialty_code, AVG(dearth_score)
        FROM dearth_scores
        WHERE geo_type = 'county'
        GROUP BY specialty_code
        """
    )
    natl_avgs = {}
    for code, avg in cur.fetchall():
        natl_avgs[code] = _round(avg)

    # Get all counties
    cur.execute(
        "SELECT fips, name, state_abbr, population FROM counties ORDER BY fips"
    )
    counties = cur.fetchall()

    # Get all specialty codes
    cur.execute("SELECT code, name FROM specialties ORDER BY name")
    specialties = cur.fetchall()

    # Get all dearth scores for counties in one query
    cur.execute(
        """
        SELECT geo_id, specialty_code,
               provider_count, provider_density,
               nearest_distance_miles, avg_distance_top3_miles,
               drive_time_minutes, wait_time_days,
               density_score, distance_score, drivetime_score, waittime_score,
               dearth_score, dearth_label
        FROM dearth_scores
        WHERE geo_type = 'county'
        """
    )
    # Index by (fips, specialty_code)
    scores_by_county = {}
    for row in cur.fetchall():
        geo_id = row[0]
        spec_code = row[1]
        scores_by_county[(geo_id, spec_code)] = row[2:]

    bundle = {}
    for fips, name, state, pop in counties:
        spec_list = []
        for spec_code, spec_name in specialties:
            score_row = scores_by_county.get((fips, spec_code))
            if score_row:
                (
                    pcount,
                    pdensity,
                    nearest_dist,
                    avg_dist,
                    drive_time,
                    wait_time,
                    density_sc,
                    distance_sc,
                    drivetime_sc,
                    waittime_sc,
                    dearth_sc,
                    dearth_lb,
                ) = score_row
                spec_list.append(
                    {
                        "code": spec_code,
                        "name": spec_name,
                        "provider_count": pcount,
                        "provider_density": _round(pdensity),
                        "nearest_distance_miles": _round(nearest_dist),
                        "avg_distance_top3_miles": _round(avg_dist),
                        "drive_time_minutes": _round(drive_time),
                        "wait_time_days": _round(wait_time),
                        "density_score": _round(density_sc),
                        "distance_score": _round(distance_sc),
                        "drivetime_score": _round(drivetime_sc),
                        "waittime_score": _round(waittime_sc),
                        "dearth_score": _round(dearth_sc),
                        "dearth_label": dearth_lb,
                        "state_avg_score": state_avgs.get((spec_code, state)),
                        "national_avg_score": natl_avgs.get(spec_code),
                    }
                )
            else:
                spec_list.append(
                    {
                        "code": spec_code,
                        "name": spec_name,
                        "provider_count": None,
                        "provider_density": None,
                        "nearest_distance_miles": None,
                        "avg_distance_top3_miles": None,
                        "drive_time_minutes": None,
                        "wait_time_days": None,
                        "density_score": None,
                        "distance_score": None,
                        "drivetime_score": None,
                        "waittime_score": None,
                        "dearth_score": None,
                        "dearth_label": None,
                        "state_avg_score": state_avgs.get((spec_code, state)),
                        "national_avg_score": natl_avgs.get(spec_code),
                    }
                )
        bundle[fips] = {
            "fips": fips,
            "name": name,
            "state": state,
            "population": pop,
            "specialties": spec_list,
        }

    path = os.path.join(out, "details", "all_counties.json")
    with open(path, "w") as f:
        f.write(_compact_json(bundle))
    print(f"  details/all_counties.json ({len(bundle)} counties)")


def export_search_index(cur, out):
    """Export search index for client-side search."""
    cur.execute(
        "SELECT fips, name, state_abbr, population FROM counties ORDER BY population DESC NULLS LAST"
    )
    counties = [
        {"id": r[0], "label": f"{r[1]}, {r[2]}", "pop": r[3]} for r in cur.fetchall()
    ]

    cur.execute(
        "SELECT zcta, state_abbr, population FROM zipcodes ORDER BY population DESC NULLS LAST"
    )
    zipcodes = [
        {"id": r[0], "label": f"{r[0]} ({r[1]})", "pop": r[2]} for r in cur.fetchall()
    ]

    index = {"counties": counties, "zipcodes": zipcodes}
    path = os.path.join(out, "search_index.json")
    with open(path, "w") as f:
        f.write(_compact_json(index))
    print(
        f"  search_index.json ({len(counties)} counties, {len(zipcodes)} zipcodes)"
    )


def export_csvs(cur, out, specialty_codes):
    """Export CSV files (one per specialty)."""
    for code in specialty_codes:
        cur.execute(
            """
            SELECT
                ds.geo_id,
                c.name, c.state_abbr AS state, c.population,
                ds.provider_count, ds.provider_density,
                ds.nearest_distance_miles, ds.avg_distance_top3_miles,
                ds.drive_time_minutes, ds.wait_time_days,
                ds.density_score, ds.distance_score,
                ds.drivetime_score, ds.waittime_score,
                ds.dearth_score, ds.dearth_label
            FROM dearth_scores ds
            JOIN counties c ON c.fips = ds.geo_id
            WHERE ds.geo_type = 'county' AND ds.specialty_code = %s
            ORDER BY ds.dearth_score DESC NULLS LAST
            """,
            (code,),
        )
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]

        path = os.path.join(out, "exports", f"dearth_county_{code}.csv")
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(colnames)
            writer.writerows(rows)
        print(f"  exports/dearth_county_{code}.csv ({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(
        description="Export API data as static JSON for GitHub Pages"
    )
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args()
    out = os.path.abspath(args.output_dir)

    print(f"Connecting to database...")
    conn = psycopg2.connect(**get_db_params())
    cur = conn.cursor()

    # Create directory structure
    for subdir in ["geojson", "counties", "details", "exports"]:
        os.makedirs(os.path.join(out, subdir), exist_ok=True)

    print(f"Exporting static data to {out}/")

    specialty_codes = export_specialties(cur, out)
    export_geojson(cur, out, specialty_codes)
    export_counties(cur, out, specialty_codes)
    export_details(cur, out)
    export_search_index(cur, out)
    export_csvs(cur, out, specialty_codes)

    cur.close()
    conn.close()
    print(f"\nStatic export complete. Files written to {out}/")


if __name__ == "__main__":
    main()

from fastapi import APIRouter, HTTPException, Query

from backend.api.database import database
from backend.api.models.schemas import CountyDetail, CountySummary, SpecialtyScore

router = APIRouter(prefix="/api/counties", tags=["counties"])


@router.get("", response_model=list[CountySummary])
async def list_counties(
    specialty: str = Query("primary_care", description="Specialty code to filter by"),
    state: str | None = Query(None, description="State abbreviation filter"),
    min_score: float | None = Query(None, description="Minimum dearth score"),
    max_score: float | None = Query(None, description="Maximum dearth score"),
):
    conditions = ["cds.specialty = :specialty"]
    params: dict = {"specialty": specialty}

    if state:
        conditions.append("cds.state_abbr = :state")
        params["state"] = state
    if min_score is not None:
        conditions.append("cds.dearth_score >= :min_score")
        params["min_score"] = min_score
    if max_score is not None:
        conditions.append("cds.dearth_score <= :max_score")
        params["max_score"] = max_score

    where = " AND ".join(conditions)
    query = f"""
        SELECT
            cds.fips,
            cds.name,
            cds.state_abbr AS state,
            cds.population,
            cds.dearth_score,
            cds.dearth_label,
            cds.provider_count,
            cds.provider_density
        FROM county_dearth_summary cds
        WHERE {where}
        ORDER BY cds.dearth_score DESC NULLS LAST
    """
    rows = await database.fetch_all(query, params)
    return [CountySummary(**dict(r._mapping)) for r in rows]


@router.get("/{fips}", response_model=CountyDetail)
async def get_county(fips: str):
    # Get county info
    county_query = """
        SELECT fips, name, state_abbr AS state, population
        FROM counties
        WHERE fips = :fips
    """
    county = await database.fetch_one(county_query, {"fips": fips})
    if not county:
        raise HTTPException(status_code=404, detail="County not found")

    # Get per-specialty scores with state and national averages
    scores_query = """
        SELECT
            s.code,
            s.name,
            ds.provider_count,
            ds.provider_density,
            ds.nearest_distance_miles,
            ds.avg_distance_top3_miles,
            ds.drive_time_minutes,
            ds.wait_time_days,
            ds.density_score,
            ds.distance_score,
            ds.drivetime_score,
            ds.waittime_score,
            ds.dearth_score,
            ds.dearth_label,
            state_avg.avg_score AS state_avg_score,
            natl_avg.avg_score AS national_avg_score
        FROM specialties s
        LEFT JOIN dearth_scores ds
            ON ds.specialty_code = s.code
            AND ds.geo_type = 'county'
            AND ds.geo_id = :fips
        LEFT JOIN LATERAL (
            SELECT AVG(ds2.dearth_score) AS avg_score
            FROM dearth_scores ds2
            JOIN counties c2 ON c2.fips = ds2.geo_id AND ds2.geo_type = 'county'
            WHERE ds2.specialty_code = s.code
              AND c2.state_abbr = (SELECT state_abbr FROM counties WHERE fips = :fips)
        ) state_avg ON TRUE
        LEFT JOIN LATERAL (
            SELECT AVG(ds3.dearth_score) AS avg_score
            FROM dearth_scores ds3
            WHERE ds3.specialty_code = s.code
              AND ds3.geo_type = 'county'
        ) natl_avg ON TRUE
        ORDER BY s.name
    """
    rows = await database.fetch_all(scores_query, {"fips": fips})

    specialties = [SpecialtyScore(**dict(r._mapping)) for r in rows]

    return CountyDetail(
        fips=county["fips"],
        name=county["name"],
        state=county["state"],
        population=county["population"],
        specialties=specialties,
    )

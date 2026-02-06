from fastapi import APIRouter, HTTPException

from backend.api.database import database
from backend.api.models.schemas import CountyDetail, SpecialtyScore

router = APIRouter(prefix="/api/zipcodes", tags=["zipcodes"])


@router.get("/{zcta}", response_model=CountyDetail)
async def get_zipcode(zcta: str):
    """Return dearth scores for a given ZIP Code Tabulation Area."""
    zip_query = """
        SELECT zcta AS fips, z.state_abbr AS state, z.population,
               COALESCE(c.name || ' (ZIP ' || z.zcta || ')', z.zcta) AS name
        FROM zipcodes z
        LEFT JOIN counties c ON c.fips = z.county_fips
        WHERE z.zcta = :zcta
    """
    ziprow = await database.fetch_one(zip_query, {"zcta": zcta})
    if not ziprow:
        raise HTTPException(status_code=404, detail="Zip code not found")

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
            AND ds.geo_type = 'zipcode'
            AND ds.geo_id = :zcta
        LEFT JOIN LATERAL (
            SELECT AVG(ds2.dearth_score) AS avg_score
            FROM dearth_scores ds2
            WHERE ds2.specialty_code = s.code
              AND ds2.geo_type = 'zipcode'
              AND ds2.geo_id IN (
                  SELECT z2.zcta FROM zipcodes z2
                  WHERE z2.state_abbr = (SELECT state_abbr FROM zipcodes WHERE zcta = :zcta)
              )
        ) state_avg ON TRUE
        LEFT JOIN LATERAL (
            SELECT AVG(ds3.dearth_score) AS avg_score
            FROM dearth_scores ds3
            WHERE ds3.specialty_code = s.code
              AND ds3.geo_type = 'zipcode'
        ) natl_avg ON TRUE
        ORDER BY s.name
    """
    rows = await database.fetch_all(scores_query, {"zcta": zcta})

    specialties = [SpecialtyScore(**dict(r._mapping)) for r in rows]

    return CountyDetail(
        fips=ziprow["fips"],
        name=ziprow["name"],
        state=ziprow["state"],
        population=ziprow["population"],
        specialties=specialties,
    )

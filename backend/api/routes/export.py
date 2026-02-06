import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from backend.api.database import database

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("")
async def export_csv(
    geo_type: str = Query("county", description="Geography type: county or zipcode"),
    specialty: str = Query("primary_care", description="Specialty code"),
    state: str | None = Query(None, description="State abbreviation filter"),
):
    conditions = ["ds.geo_type = :geo_type", "ds.specialty_code = :specialty"]
    params: dict = {"geo_type": geo_type, "specialty": specialty}

    if geo_type == "county":
        join = "JOIN counties c ON c.fips = ds.geo_id"
        select_extra = "c.name, c.state_abbr AS state, c.population"
        if state:
            conditions.append("c.state_abbr = :state")
            params["state"] = state
    else:
        join = "JOIN zipcodes z ON z.zcta = ds.geo_id"
        select_extra = "z.zcta AS name, z.state_abbr AS state, z.population"
        if state:
            conditions.append("z.state_abbr = :state")
            params["state"] = state

    where = " AND ".join(conditions)
    query = f"""
        SELECT
            ds.geo_id,
            {select_extra},
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
            ds.dearth_label
        FROM dearth_scores ds
        {join}
        WHERE {where}
        ORDER BY ds.dearth_score DESC NULLS LAST
    """

    rows = await database.fetch_all(query, params)

    output = io.StringIO()
    if rows:
        fieldnames = list(rows[0]._mapping.keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row._mapping))
    else:
        output.write("No data found\n")

    output.seek(0)
    filename = f"dearth_{geo_type}_{specialty}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.api.database import database

router = APIRouter(prefix="/api/geojson", tags=["geojson"])


@router.get("/counties")
async def counties_geojson(
    specialty: str = Query("primary_care", description="Specialty code"),
):
    """
    Return a GeoJSON FeatureCollection of all counties with dearth scores
    for the given specialty. Geometry is omitted — the frontend merges
    these properties with us-atlas TopoJSON geometry on FIPS code.
    """
    query = """
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
        WHERE cds.specialty = :specialty
        ORDER BY cds.fips
    """
    rows = await database.fetch_all(query, {"specialty": specialty})

    features = []
    for r in rows:
        features.append(
            {
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "fips": r["fips"],
                    "name": r["name"],
                    "state": r["state"],
                    "population": r["population"],
                    "dearth_score": float(r["dearth_score"]) if r["dearth_score"] is not None else 0,
                    "dearth_label": r["dearth_label"] or "N/A",
                    "provider_count": r["provider_count"],
                    "provider_density": float(r["provider_density"]) if r["provider_density"] is not None else 0,
                },
            }
        )

    collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    return JSONResponse(content=collection)

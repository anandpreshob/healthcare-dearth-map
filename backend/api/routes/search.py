from fastapi import APIRouter, Query

from backend.api.database import database
from backend.api.models.schemas import SearchResult

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search(q: str = Query(..., min_length=1, description="Search query")):
    pattern = f"%{q}%"

    query = """
        (
            SELECT 'county' AS type,
                   fips AS id,
                   name || ', ' || state_abbr AS label
            FROM counties
            WHERE name ILIKE :pattern OR fips ILIKE :pattern
            ORDER BY population DESC NULLS LAST
            LIMIT 10
        )
        UNION ALL
        (
            SELECT 'zipcode' AS type,
                   zcta AS id,
                   zcta || ' (' || state_abbr || ')' AS label
            FROM zipcodes
            WHERE zcta ILIKE :pattern
            ORDER BY population DESC NULLS LAST
            LIMIT 10
        )
        LIMIT 10
    """
    rows = await database.fetch_all(query, {"pattern": pattern})
    return [SearchResult(**dict(r._mapping)) for r in rows]

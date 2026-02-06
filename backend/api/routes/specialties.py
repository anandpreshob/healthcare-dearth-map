from fastapi import APIRouter

from backend.api.database import database
from backend.api.models.schemas import Specialty

router = APIRouter(prefix="/api/specialties", tags=["specialties"])


@router.get("", response_model=list[Specialty])
async def list_specialties():
    query = "SELECT code, name FROM specialties ORDER BY name"
    rows = await database.fetch_all(query)
    return [Specialty(code=r["code"], name=r["name"]) for r in rows]

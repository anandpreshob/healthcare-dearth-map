from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.config import settings
from backend.api.database import connect, disconnect
from backend.api.routes import counties, export, geojson, search, specialties, zipcodes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    yield
    await disconnect()


app = FastAPI(
    title="US Healthcare Dearth Map API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(specialties.router)
app.include_router(counties.router)
app.include_router(zipcodes.router)
app.include_router(search.router)
app.include_router(export.router)
app.include_router(geojson.router)


@app.get("/")
async def root():
    return {"status": "ok"}

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# --- Specialty ---

class Specialty(BaseModel):
    code: str
    name: str


# --- County list item ---

class CountySummary(BaseModel):
    fips: str
    name: str
    state: str
    population: int | None
    dearth_score: float | None
    dearth_label: str | None
    provider_count: int | None
    provider_density: float | None


# --- Per-specialty breakdown inside a county/zip detail ---

class SpecialtyScore(BaseModel):
    code: str
    name: str
    provider_count: int | None
    provider_density: float | None
    nearest_distance_miles: float | None
    avg_distance_top3_miles: float | None
    drive_time_minutes: float | None
    wait_time_days: float | None
    density_score: float | None
    distance_score: float | None
    drivetime_score: float | None
    waittime_score: float | None
    dearth_score: float | None
    dearth_label: str | None
    state_avg_score: float | None
    national_avg_score: float | None


# --- County detail (single county with all specialty scores) ---

class CountyDetail(BaseModel):
    fips: str
    name: str
    state: str
    population: int | None
    specialties: list[SpecialtyScore]


# --- Search ---

class SearchResult(BaseModel):
    type: str  # "county" or "zipcode"
    id: str
    label: str


# --- GeoJSON ---

class GeoJSONProperties(BaseModel):
    fips: str
    name: str
    state: str
    population: int | None
    dearth_score: float | None
    dearth_label: str | None
    provider_count: int | None
    provider_density: float | None


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: GeoJSONProperties


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]

"""
API v1 router aggregator.

All domain routers are registered here and mounted under /api/v1 in main.py.
Adding a new domain module = one include_router call.
"""

from fastapi import APIRouter

from app.api.crops.router import router as crops_router
from app.api.disease_observations.router import router as disease_observations_router
from app.api.fields.router import router as fields_router
from app.api.health.router import router as health_router
from app.api.irrigation_events.router import router as irrigation_events_router
from app.api.satellite_observations.router import router as satellite_observations_router
from app.api.sensor_readings.router import router as sensor_readings_router
from app.api.soil_profiles.router import router as soil_profiles_router
from app.api.version.router import router as version_router
from app.api.weather_records.router import router as weather_records_router
from app.api.yield_records.router import router as yield_records_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(version_router)
api_router.include_router(fields_router)
api_router.include_router(crops_router)
api_router.include_router(disease_observations_router)
api_router.include_router(soil_profiles_router)
api_router.include_router(weather_records_router)
api_router.include_router(sensor_readings_router)
api_router.include_router(satellite_observations_router)
api_router.include_router(irrigation_events_router)
api_router.include_router(yield_records_router)

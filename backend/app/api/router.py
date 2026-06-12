"""
API v1 router aggregator.

All domain routers are registered here and mounted under /api/v1 in main.py.
Adding a new domain module = one include_router call.
"""

from fastapi import APIRouter

from app.api.crops.router import router as crops_router
from app.api.fields.router import router as fields_router
from app.api.health.router import router as health_router
from app.api.version.router import router as version_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(version_router)
api_router.include_router(fields_router)
api_router.include_router(crops_router)

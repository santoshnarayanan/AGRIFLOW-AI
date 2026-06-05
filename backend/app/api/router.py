"""
API v1 router aggregator.

All domain routers are registered here and mounted under /api/v1 in main.py.
Adding a new domain module = one include_router call.
"""

from fastapi import APIRouter

from app.api.health.router import router as health_router
from app.api.version.router import router as version_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(version_router)

# Future domain routers will be added here, e.g.:
# from app.api.farms.router import router as farms_router
# api_router.include_router(farms_router)

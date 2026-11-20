"""API Route definitions and endpoint routers."""

from fastapi import APIRouter
from app.routers import health, analyze, heatmaps

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(analyze.router, tags=["Analysis"])
api_router.include_router(heatmaps.router, tags=["Heatmaps"])

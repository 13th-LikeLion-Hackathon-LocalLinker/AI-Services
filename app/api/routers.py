from fastapi import APIRouter

from app.api.endpoints import health, benefits

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(benefits.router, prefix="/benefits", tags=["benefits"])

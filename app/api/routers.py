from fastapi import APIRouter

from app.api.endpoints import health, chatbot, translation

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])
api_router.include_router(translation.router, prefix="/translation", tags=["translation"])

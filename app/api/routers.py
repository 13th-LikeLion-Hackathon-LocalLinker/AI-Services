from fastapi import APIRouter

from app.api.endpoints import health, benefits, chatbot

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(benefits.router, prefix="/benefits", tags=["benefits"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])

from fastapi import FastAPI

from app.api.routers import api_router

app = FastAPI(
    title="LocalLinker AI service",
    description="로컬링커 팀 AI 서비스 API입니다.",
    version="0.0.1"
)

app.include_router(api_router, prefix="/api/v1")
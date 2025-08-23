from typing import Optional, Literal

from pydantic import BaseModel, Field

class ChatbotReq(BaseModel):
    """챗봇 요청 DTO"""
    query: str = Field(..., description="사용자 질의")
    lang: Literal["ko", "zh", "th", "en", "vi", "ja", "uz"] = Field("ko", description="질의 언어")

class TranslationReq(BaseModel):
    """번역 요청 DTO (여러 필드 번역)"""
    title: str = Field(..., description="번역할 제목", min_length=1, max_length=1000)
    eligibility: str = Field(..., description="번역할 자격요건", min_length=1, max_length=3000)
    text: str = Field(..., description="번역할 본문 텍스트", min_length=1, max_length=5000)
    target_language: Literal["ko", "zh", "th", "en", "vi", "ja", "uz"] = Field(..., description="번역 대상 언어")


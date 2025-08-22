from typing import Optional, Literal

from pydantic import BaseModel, Field

class ChatbotReq(BaseModel):
    """챗봇 요청 DTO"""
    query: str = Field(..., description="사용자 질의")
    lang: Literal["ko", "zh", "th", "en", "vi", "ja", "uz"] = Field("ko", description="질의 언어")

class TranslationReq(BaseModel):
    """번역 요청 DTO (한국어 -> 다른 언어)"""
    text: str = Field(..., description="번역할 한국어 텍스트", min_length=1, max_length=5000)
    target_language: Literal["zh", "th", "en", "vi", "ja", "uz"] = Field(..., description="번역 대상 언어 (한국어 제외)")


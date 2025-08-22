from typing import Optional, Literal

from pydantic import BaseModel, Field

class ChatbotReq(BaseModel):
    """챗봇 요청 DTO"""
    query: str = Field(..., description="사용자 질의")
    lang: Literal["ko", "zh", "th", "en", "vi", "ja", "uz"] = Field("ko", description="질의 언어")

class TranslationReq(BaseModel):
    """번역 요청 DTO"""
    text: str = Field(..., description="번역할 텍스트", min_length=1, max_length=5000)
    target_language: Literal["ko", "zh", "th", "en", "vi", "ja", "uz"] = Field(..., description="번역 대상 언어")
    source_language: Optional[Literal["ko", "zh", "th", "en", "vi", "ja", "uz"]] = Field(None, description="원본 언어 (자동 감지시 생략 가능)")


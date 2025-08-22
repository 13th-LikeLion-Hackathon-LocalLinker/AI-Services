from pydantic import BaseModel, Field

class ChatbotRes(BaseModel):
    """챗봇 응답 DTO"""
    answer: str = Field(..., description="챗봇의 답변")

class TranslationRes(BaseModel):
    """번역 응답 DTO (한국어 -> 다른 언어)"""
    translated_text: str = Field(..., description="번역된 텍스트")
    target_language: str = Field(..., description="번역 대상 언어")
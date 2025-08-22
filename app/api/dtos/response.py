from pydantic import BaseModel, Field

class ChatbotRes(BaseModel):
    """챗봇 응답 DTO"""
    answer: str = Field(..., description="챗봇의 답변")

class TranslationRes(BaseModel):
    """번역 응답 DTO"""
    translated_text: str = Field(..., description="번역된 텍스트")
    source_language: str = Field(..., description="감지된 원본 언어")
    target_language: str = Field(..., description="번역 대상 언어")
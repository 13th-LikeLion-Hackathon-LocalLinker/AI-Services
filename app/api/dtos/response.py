from pydantic import BaseModel, Field

class ChatbotRes(BaseModel):
    """챗봇 응답 DTO"""
    answer: str = Field(..., description="챗봇의 답변")

class TranslationRes(BaseModel):
    """번역 응답 DTO (여러 필드 번역 결과)"""
    title: str = Field(..., description="번역된 제목")
    eligibility: str = Field(..., description="번역된 자격요건")
    text: str = Field(..., description="번역된 본문 텍스트")
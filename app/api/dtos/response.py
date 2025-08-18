from typing import List, Optional
from pydantic import BaseModel

class BenefitHit(BaseModel):
    """개별 혜택 프로그램 정보 DTO"""
    program_id: str
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    category: Optional[str] = None
    name: Optional[str] = None
    desc: Optional[str] = None
    apply_url: Optional[str] = None
    source_url: Optional[str] = None
    featured: bool = False
    updated_at: Optional[str] = None
    score: float

class BenefitsSearchRes(BaseModel):
    """혜택 프로그램 검색 응답 DTO"""
    total: int
    page: int
    size: int
    items: List[BenefitHit]

class ChatbotRes(BaseModel):
    """챗봇 응답 DTO"""
    answer: str
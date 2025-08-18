from typing import Optional, Literal
from pydantic import BaseModel, Field

class BenefitsSearchReq(BaseModel):
    """혜택 프로그램 검색 요청 DTO"""
    query: str = Field(..., description="자연어 질의")
    lang: str = Field("ko", pattern="^(ko|zh|th|en|vi|ja|uz)$")
    visa: Optional[str] = None
    jurisdiction: Optional[str] = None  # CHEONAN / CHUNGCHEONGNAM / NATIONAL
    category: Optional[str] = None      # ADMIN|HEALTH|HOUSING|EDUCATION|EMPLOYMENT|TAX
    k: int = Field(30, ge=1, le=100)
    page: int = Field(0, ge=0)
    size: int = Field(10, ge=1, le=50)

class ChatbotReq(BaseModel):
    """챗봇 요청 DTO"""
    query: str = Field(..., description="사용자 질의")
    lang: Literal["ko", "zh", "th", "en", "vi", "ja", "uz"] = Field("ko", description="질의 언어")
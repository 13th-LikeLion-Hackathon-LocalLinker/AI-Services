"""
번역 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.api.dtos.request import TranslationReq
from app.api.dtos.response import TranslationRes
from app.services.OpenAIService import OpenAIService

router = APIRouter()

@router.post("/translate", response_model=TranslationRes)
async def translate_korean_text(request: TranslationReq):
    """
    한국어 다중 필드 번역 API
    
    Args:
        request: 번역 요청 정보 (제목, 자격요건, 본문, 대상 언어)
        
    Returns:
        번역 결과 (번역된 제목, 자격요건, 본문)
    """
    try:
        logger.info(f"한국어 다중 필드 번역 요청 - 대상 언어: {request.target_language}")
        logger.info(f"제목 길이: {len(request.title)}, 자격요건 길이: {len(request.eligibility)}, 본문 길이: {len(request.text)}")
        
        # OpenAI 서비스 인스턴스 생성
        openai_service = OpenAIService()
        
        # 한국어 → 대상 언어 다중 필드 번역 수행
        translation_result = openai_service.translate_multiple_fields(
            title=request.title,
            eligibility=request.eligibility,
            text=request.text,
            target_language=request.target_language
        )
        
        logger.info(f"다중 필드 번역 성공 - 한국어 -> {request.target_language}")
        
        return TranslationRes(**translation_result)
        
    except Exception as e:
        logger.error(f"번역 API 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"번역 처리 중 오류가 발생했습니다: {str(e)}"
        )

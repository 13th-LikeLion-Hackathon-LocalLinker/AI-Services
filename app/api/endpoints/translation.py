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
    한국어 텍스트 번역 API (최적화됨)
    
    Args:
        request: 번역 요청 정보 (한국어 텍스트, 대상 언어)
        
    Returns:
        번역 결과 (번역된 텍스트, 대상 언어)
    """
    try:
        logger.info(f"한국어 번역 요청 - 대상 언어: {request.target_language}, 텍스트 길이: {len(request.text)}")
        
        # OpenAI 서비스 인스턴스 생성
        openai_service = OpenAIService()
        
        # 한국어 → 대상 언어 번역 수행
        translation_result = openai_service.translate_korean_to_target(
            text=request.text,
            target_language=request.target_language
        )
        
        logger.info(f"번역 성공 - 한국어 -> {translation_result['target_language']}")
        
        return TranslationRes(**translation_result)
        
    except Exception as e:
        logger.error(f"번역 API 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"번역 처리 중 오류가 발생했습니다: {str(e)}"
        )

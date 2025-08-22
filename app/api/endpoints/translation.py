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
async def translate_text(request: TranslationReq):
    """
    텍스트 번역 API
    
    Args:
        request: 번역 요청 정보 (텍스트, 대상 언어, 원본 언어)
        
    Returns:
        번역 결과 (번역된 텍스트, 감지된 원본 언어, 대상 언어)
    """
    try:
        logger.info(f"번역 요청 - 대상 언어: {request.target_language}, 텍스트 길이: {len(request.text)}")
        
        # OpenAI 서비스 인스턴스 생성
        openai_service = OpenAIService()
        
        # 번역 수행
        translation_result = openai_service.translate_text(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language
        )
        
        logger.info(f"번역 성공 - {translation_result['source_language']} -> {translation_result['target_language']}")
        
        return TranslationRes(**translation_result)
        
    except Exception as e:
        logger.error(f"번역 API 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"번역 처리 중 오류가 발생했습니다: {str(e)}"
        )

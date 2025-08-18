from fastapi import APIRouter

from app.api.dtos.request import ChatbotReq
from app.api.dtos.response import ChatbotRes
from app.services.rag_service import RAGService
from loguru import logger

router = APIRouter()

rag_service = RAGService()

@router.get("/health")
def health():
    """Chatbot service health check endpoint"""
    return {
        "ok": True,
        "message": "Chatbot service is healthy"
    }


@router.post("/ask", response_model=ChatbotRes)
async def ask_question(request: ChatbotReq) -> ChatbotRes:
    try:
        logger.info(f"RAG API 호출: '{request.query}' (언어: {request.lang})")

        # RAG 서비스로 질문 처리
        response = rag_service.process_question(request)

        logger.info(f"RAG API 응답 완료: {len(response.answer)}자")

        return response

    except Exception as e:
        logger.error(f"RAG API 오류: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail="질문 처리 중 오류가 발생했습니다."
        )

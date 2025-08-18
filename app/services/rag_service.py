"""
RAG (Retrieval-Augmented Generation) 서비스
"""
import time
from typing import List, Dict, Any
from loguru import logger

from app.api.dtos.request import ChatbotReq
from app.api.dtos.response import ChatbotRes
from app.services.vector_search_service import VectorSearchService
from app.services.OpenAIService import OpenAIService


class RAGService:
	"""RAG 질문 처리 핵심 로직"""

	def __init__(self) -> None:
		self.vector_search = VectorSearchService()
		self.openai_service = OpenAIService()

	def process_question(self, request: ChatbotReq) -> ChatbotRes:
		start_time = time.time()
		try:
			logger.info(f"RAG 처리 시작: '{request.query}' (언어: {request.lang})")

			# 1) 관련 청크 검색
			logger.info("벡터 검색 서비스 호출 중...")
			relevant = self.vector_search.search_relevant_chunks(
				question=request.query, language=request.lang
			)
			logger.info(f"벡터 검색 완료: {len(relevant)}개 결과")

			if not relevant:
				logger.warning("관련 정보를 찾을 수 없음")
				return ChatbotRes(
					answer="죄송합니다. 질문과 관련된 정보를 찾을 수 없습니다."
				)

			# 2) 컨텍스트 구성
			logger.info("컨텍스트 구성 중...")
			context = self.vector_search.get_search_summary(relevant)
			logger.info(f"컨텍스트 길이: {len(context)} 문자")

			# 3) LLM 호출
			logger.info("OpenAI API 호출 중...")
			answer = self.openai_service.generate_rag_answer(
				question=request.query, context=context, language=request.lang
			)
			logger.info("OpenAI API 호출 완료")

			# 4) 부가 정보 생성
			sources = self._extract_sources(relevant)
			confidence = self._calculate_confidence_score(relevant)

			logger.info(f"RAG 처리 완료: {time.time() - start_time:.2f}초")
			return ChatbotRes(
				answer=answer
			)
		except Exception as e:
			logger.error(f"RAG 처리 오류: {str(e)}", exc_info=True)
			return ChatbotRes(
				answer="죄송합니다. 질문 처리 중 오류가 발생했습니다."
			)

	def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[str]:
		sources: List[str] = []
		for chunk in chunks:
			file_name = chunk.get("file_name", "")
			page_range = chunk.get("page_range", "")
			toc_title = chunk.get("toc_title", "")
			entry = file_name
			if page_range:
				entry += f" (페이지 {page_range})"
			if toc_title:
				entry += f" - {toc_title}"
			sources.append(entry)
		return sources

	def _calculate_confidence_score(self, chunks: List[Dict[str, Any]]) -> float:
		if not chunks:
			return 0.0
		scores = [float(c.get("score", 0.0)) for c in chunks]
		avg = sum(scores) / len(scores)
		return round(max(0.0, min(1.0, avg)), 2)
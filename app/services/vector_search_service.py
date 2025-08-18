"""
벡터 검색 서비스 (Qdrant + ETL 재사용)
"""
from typing import List, Dict, Any
from loguru import logger

from etl.qdrant_service import QdrantService
from app.config.OpenAIConfig import openai_config

class VectorSearchService:
	"""질문과 관련된 청크를 Qdrant에서 조회"""

	def __init__(self) -> None:
		self.qdrant = QdrantService()
		self.top_k = openai_config.top_k_results

	def search_relevant_chunks(self, question: str, language: str = "ko") -> List[Dict[str, Any]]:
		"""
		질문과 관련된 청크 검색 (언어 필터 적용)
		"""
		try:
			filters = {"language": language}
			results = self.qdrant.search_by_text(query_text=question, limit=self.top_k, filters=filters)
			logger.info(f"질문 '{question}' 관련 결과 {len(results)}개")
			return results
		except Exception as e:
			logger.error(f"벡터 검색 중 오류: {str(e)}")
			return []

	def get_search_summary(self, chunks: List[Dict[str, Any]]) -> str:
		"""검색된 청크들을 요약하여 컨텍스트 문자열 생성"""
		if not chunks:
			return "관련 정보를 찾을 수 없습니다."

		parts: List[str] = []
		for i, chunk in enumerate(chunks, 1):
			file_name = chunk.get("file_name", "")
			page_range = chunk.get("page_range", "")
			toc_title = chunk.get("toc_title", "")
			content = chunk.get("content", "")

			header = f"[{i}] {file_name}"
			if page_range:
				header += f" (페이지 {page_range})"
			if toc_title:
				header += f" - {toc_title}"

			parts.append(f"{header}\n{content}\n")

		return "\n".join(parts)

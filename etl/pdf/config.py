"""
ETL 설정 관리
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.embeddings import OpenAIEmbeddings

# .env 파일 로드
load_dotenv()


class ETLConfig:
    """ETL 설정 클래스"""

    def __init__(self):
        # 프로젝트 루트 경로
        self.project_root = Path(__file__).parent.parent.parent

        # PDF 가이드북 경로
        self.guidebook_dir = self.project_root / "guidebook_pdfs"

        # faiss 인덱스 경로
        self.faiss_index_dir = Path(__file__).parent / "faiss_index"

        # 청킹 설정
        self.chunk_size = 1000  # 토큰 기준 청크 크기
        self.chunk_overlap = 0  # 청크 간 겹치는 토큰 수

        # OpenAI 설정
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_model = OpenAIEmbeddings(chunk_size=self.chunk_size)

        # 지원 언어
        self.supported_languages = {
            "ko": "한국어",
            "en": "영어",
            "ja": "일본어",
            "zh": "중국어",
            "vi": "베트남어",
            "uz": "우즈벡어",
            "th": "태국어"
        }

# 전역 설정 인스턴스
config = ETLConfig()

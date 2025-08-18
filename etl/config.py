"""
ETL 설정 관리
"""
import os
from pathlib import Path
from typing import Dict, Any

class ETLConfig:
    """ETL 설정 클래스"""
    
    def __init__(self):
        # 프로젝트 루트 경로
        self.project_root = Path(__file__).parent.parent
        
        # PDF 가이드북 경로
        self.guidebook_dir = self.project_root / "guidebook_pdfs"
        
        # 청킹 설정
        self.chunk_size = 1000  # 토큰 기준 청크 크기
        self.chunk_overlap = 200  # 청크 간 겹치는 토큰 수
        
        # Qdrant 설정
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = "guidebook_chunks"
        
        # 임베딩 모델 설정
        self.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        self.embedding_dimension = 384
        
        # 청킹 전략
        self.chunking_strategies = {
            "table_of_contents": "목차 기반 청킹",
            "semantic": "의미적 청킹",
            "fixed_size": "고정 크기 청킹"
        }
        
        # 지원 언어
        self.supported_languages = {
            "ko": "한국어",
            "en": "영어", 
            "ja": "일본어",
            "zh": "중국어",
            "vi": "베트남어",
            "uz": "우즈벡어"
        }

# 전역 설정 인스턴스
config = ETLConfig()


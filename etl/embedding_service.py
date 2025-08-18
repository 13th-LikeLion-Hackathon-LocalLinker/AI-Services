"""
텍스트 임베딩 생성 서비스
"""
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger
from .config import config

class EmbeddingService:
    """텍스트 임베딩 생성 서비스"""
    
    def __init__(self):
        self.model_name = config.embedding_model
        self.dimension = config.embedding_dimension
        
        try:
            logger.info(f"임베딩 모델 로딩 중: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("임베딩 모델 로딩 완료")
        except Exception as e:
            logger.error(f"임베딩 모델 로딩 실패: {str(e)}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 리스트에 대한 임베딩 생성
        
        Args:
            texts: 임베딩을 생성할 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        try:
            logger.info(f"{len(texts)}개 텍스트에 대한 임베딩 생성 시작")
            
            # 배치 처리로 임베딩 생성
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                normalize_embeddings=True
            )
            
            # numpy 배열을 리스트로 변환
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            
            logger.info(f"임베딩 생성 완료: {len(embeddings)}개")
            return embeddings
            
        except Exception as e:
            logger.error(f"임베딩 생성 중 오류 발생: {str(e)}")
            raise
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """
        단일 텍스트에 대한 임베딩 생성
        
        Args:
            text: 임베딩을 생성할 텍스트
            
        Returns:
            임베딩 벡터
        """
        try:
            embedding = self.model.encode([text], normalize_embeddings=True)
            
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            return embedding[0]
            
        except Exception as e:
            logger.error(f"단일 임베딩 생성 중 오류 발생: {str(e)}")
            raise
    
    def batch_generate_embeddings_with_metadata(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        청크 데이터에 임베딩을 추가하여 반환
        
        Args:
            chunks: 청크 데이터 리스트
            
        Returns:
            임베딩이 추가된 청크 데이터 리스트
        """
        try:
            # 텍스트만 추출
            texts = [chunk['content'] for chunk in chunks]
            
            # 임베딩 생성
            embeddings = self.generate_embeddings(texts)
            
            # 청크에 임베딩 추가
            for i, chunk in enumerate(chunks):
                chunk['embedding'] = embeddings[i]
                chunk['embedding_dimension'] = self.dimension
            
            logger.info(f"{len(chunks)}개 청크에 임베딩 추가 완료")
            return chunks
            
        except Exception as e:
            logger.error(f"청크 임베딩 생성 중 오류 발생: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        현재 로드된 모델 정보 반환
        
        Returns:
            모델 정보 딕셔너리
        """
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'max_seq_length': self.model.max_seq_length if hasattr(self.model, 'max_seq_length') else None
        }
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        임베딩 벡터 유효성 검증
        
        Args:
            embedding: 검증할 임베딩 벡터
            
        Returns:
            유효성 여부
        """
        try:
            if not isinstance(embedding, list):
                return False
            
            if len(embedding) != self.dimension:
                return False
            
            # NaN이나 무한대 값 체크
            if any(not np.isfinite(val) for val in embedding):
                return False
            
            return True
            
        except Exception:
            return False
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        두 임베딩 벡터 간의 코사인 유사도 계산
        
        Args:
            embedding1: 첫 번째 임베딩 벡터
            embedding2: 두 번째 임베딩 벡터
            
        Returns:
            코사인 유사도 (0~1)
        """
        try:
            if not (self.validate_embedding(embedding1) and self.validate_embedding(embedding2)):
                return 0.0
            
            # numpy 배열로 변환
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 코사인 유사도 계산
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"유사도 계산 중 오류 발생: {str(e)}")
            return 0.0


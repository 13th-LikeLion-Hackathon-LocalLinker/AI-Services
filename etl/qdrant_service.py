"""
Qdrant 벡터 데이터베이스 서비스
"""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, MatchValue, Range
)
from loguru import logger
from .config import config

class QdrantService:
    """Qdrant 벡터 데이터베이스 서비스"""
    
    def __init__(self):
        self.host = config.qdrant_host
        self.port = config.qdrant_port
        self.collection_name = config.collection_name
        self.embedding_dimension = config.embedding_dimension
        
        try:
            logger.info(f"Qdrant 클라이언트 연결 중: {self.host}:{self.port}")
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info("Qdrant 클라이언트 연결 완료")
        except Exception as e:
            logger.error(f"Qdrant 클라이언트 연결 실패: {str(e)}")
            raise
    
    def create_collection(self, force_recreate: bool = False) -> bool:
        """
        컬렉션 생성
        
        Args:
            force_recreate: 기존 컬렉션을 삭제하고 새로 생성할지 여부
            
        Returns:
            생성 성공 여부
        """
        try:
            # 기존 컬렉션 확인
            collections = self.client.get_collections()
            collection_exists = any(
                col.name == self.collection_name for col in collections.collections
            )
            
            if collection_exists:
                if force_recreate:
                    logger.info(f"기존 컬렉션 삭제 중: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"컬렉션이 이미 존재합니다: {self.collection_name}")
                    return True
            
            # 새 컬렉션 생성
            logger.info(f"새 컬렉션 생성 중: {self.collection_name}")
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"컬렉션 생성 완료: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"컬렉션 생성 중 오류 발생: {str(e)}")
            return False
    
    def insert_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        청크 데이터를 벡터 DB에 삽입
        
        Args:
            chunks: 임베딩이 포함된 청크 데이터 리스트
            
        Returns:
            삽입 성공 여부
        """
        try:
            if not chunks:
                logger.warning("삽입할 청크가 없습니다.")
                return True
            
            logger.info(f"{len(chunks)}개 청크 삽입 시작")
            
            # PointStruct로 변환
            points = []
            for chunk in chunks:
                if 'embedding' not in chunk:
                    logger.warning(f"임베딩이 없는 청크 건너뛰기: {chunk.get('chunk_id', 'unknown')}")
                    continue
                
                point = PointStruct(
                    id=chunk['chunk_id'],
                    vector=chunk['embedding'],
                    payload={
                        'content': chunk['content'],
                        'metadata': chunk.get('metadata', {}),
                        'chunk_type': chunk.get('metadata', {}).get('chunk_type', 'unknown'),
                        'language': chunk.get('metadata', {}).get('language', 'unknown'),
                        'file_name': chunk.get('metadata', {}).get('file_name', ''),
                        'page_range': f"{chunk.get('metadata', {}).get('start_page', '')}-{chunk.get('metadata', {}).get('end_page', '')}",
                        'toc_title': chunk.get('metadata', {}).get('toc_title', ''),
                        'toc_level': chunk.get('metadata', {}).get('toc_level', 0),
                        'created_at': chunk.get('created_at', ''),
                        'source_file': chunk.get('source_file', '')
                    }
                )
                points.append(point)
            
            if not points:
                logger.warning("유효한 포인트가 없습니다.")
                return False
            
            # 배치 삽입
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"{len(points)}개 청크 삽입 완료")
            return True
            
        except Exception as e:
            logger.error(f"청크 삽입 중 오류 발생: {str(e)}")
            return False
    
    def search_similar(self, query_embedding: List[float], limit: int = 10, 
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        유사한 벡터 검색
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            limit: 반환할 결과 수
            filters: 검색 필터
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 필터 구성
            search_filter = None
            if filters:
                search_filter = self._build_search_filter(filters)
            
            # 벡터 검색
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False
            )
            
            # 결과 변환
            results = []
            for point in search_result:
                result = {
                    'id': point.id,
                    'score': point.score,
                    'content': point.payload.get('content', ''),
                    'metadata': point.payload.get('metadata', {}),
                    'chunk_type': point.payload.get('chunk_type', ''),
                    'language': point.payload.get('language', ''),
                    'file_name': point.payload.get('file_name', ''),
                    'page_range': point.payload.get('page_range', ''),
                    'toc_title': point.payload.get('toc_title', '')
                }
                results.append(result)
            
            logger.info(f"검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"벡터 검색 중 오류 발생: {str(e)}")
            return []
    
    def search_by_text(self, query_text: str, limit: int = 10,
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        텍스트로 검색 (임베딩 생성 후 검색)
        
        Args:
            query_text: 검색할 텍스트
            limit: 반환할 결과 수
            filters: 검색 필터
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 임베딩 서비스 임포트 (순환 참조 방지)
            from .embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.generate_single_embedding(query_text)
            
            return self.search_similar(query_embedding, limit, filters)
            
        except Exception as e:
            logger.error(f"텍스트 검색 중 오류 발생: {str(e)}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """
        컬렉션 정보 조회

        Returns:
            컬렉션 정보 딕셔너리
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)

            return {
                'name': collection_info.name,
                'vectors_count': collection_info.vectors_count,
                'points_count': collection_info.points_count,
                'status': collection_info.status,
                'config': {
                    'vector_size': collection_info.config.params.vectors.size,
                    'distance': collection_info.config.params.vectors.distance
                }
            }

        except Exception as e:
            logger.error(f"컬렉션 정보 조회 중 오류 발생: {str(e)}")
            return {}

    def delete_collection(self) -> bool:
        """
        컬렉션 삭제
        
        Returns:
            삭제 성공 여부
        """
        try:
            logger.info(f"컬렉션 삭제 중: {self.collection_name}")
            self.client.delete_collection(self.collection_name)
            logger.info(f"컬렉션 삭제 완료: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"컬렉션 삭제 중 오류 발생: {str(e)}")
            return False
    
    def _build_search_filter(self, filters: Dict[str, Any]) -> Filter:
        """
        검색 필터 구성
        
        Args:
            filters: 필터 조건 딕셔너리
            
        Returns:
            Qdrant Filter 객체
        """
        conditions = []
        
        # 언어 필터
        if 'language' in filters and filters['language']:
            conditions.append(
                FieldCondition(key="language", match=MatchValue(value=filters['language']))
            )
        
        # 청크 타입 필터
        if 'chunk_type' in filters and filters['chunk_type']:
            conditions.append(
                FieldCondition(key="chunk_type", match=MatchValue(value=filters['chunk_type']))
            )
        
        # 파일명 필터
        if 'file_name' in filters and filters['file_name']:
            conditions.append(
                FieldCondition(key="file_name", match=MatchValue(value=filters['file_name']))
            )
        
        # TOC 레벨 필터
        if 'toc_level' in filters and filters['toc_level'] is not None:
            conditions.append(
                FieldCondition(key="toc_level", range=Range(gte=filters['toc_level']))
            )
        
        return Filter(must=conditions) if conditions else None
    
    def health_check(self) -> bool:
        """
        서비스 상태 확인
        
        Returns:
            정상 여부
        """
        try:
            # 간단한 API 호출로 상태 확인
            self.client.get_collections()
            return True
        except Exception:
            return False


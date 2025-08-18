"""
ETL 파이프라인 메인 클래스
PDF 처리부터 벡터 DB 저장까지 전체 과정을 조율
"""
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
from .config import config
from .pdf_processor import PDFProcessor
from .text_chunker import TextChunker
from .embedding_service import EmbeddingService
from .qdrant_service import QdrantService

class ETLPipeline:
    """ETL 파이프라인 메인 클래스"""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.text_chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
        
        # 처리 통계
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_chunks': 0,
            'successful_chunks': 0,
            'failed_chunks': 0,
            'start_time': None,
            'end_time': None
        }
    
    def run_full_pipeline(self, force_recreate_collection: bool = False) -> bool:
        """
        전체 ETL 파이프라인 실행
        
        Args:
            force_recreate_collection: 기존 컬렉션을 삭제하고 새로 생성할지 여부
            
        Returns:
            성공 여부
        """
        try:
            logger.info("=== ETL 파이프라인 시작 ===")
            self.stats['start_time'] = datetime.now()
            
            # 1. Qdrant 컬렉션 생성
            if not self._setup_database(force_recreate_collection):
                return False
            
            # 2. PDF 파일 목록 가져오기
            pdf_files = self.pdf_processor.get_pdf_files()
            if not pdf_files:
                logger.warning("처리할 PDF 파일이 없습니다.")
                return False
            
            self.stats['total_files'] = len(pdf_files)
            logger.info(f"처리할 PDF 파일 수: {len(pdf_files)}")
            
            # 3. 각 PDF 파일 처리
            for pdf_file in pdf_files:
                if not self._process_single_pdf(pdf_file):
                    logger.warning(f"PDF 처리 실패: {pdf_file.name}")
                    continue
                
                self.stats['processed_files'] += 1
            
            # 4. 파이프라인 완료
            self.stats['end_time'] = datetime.now()
            self._print_final_stats()
            
            logger.info("=== ETL 파이프라인 완료 ===")
            return True
            
        except Exception as e:
            logger.error(f"ETL 파이프라인 실행 중 오류 발생: {str(e)}")
            return False
    
    def process_single_pdf(self, pdf_path: Path, chunking_strategy: str = 'auto') -> bool:
        """
        단일 PDF 파일 처리
        
        Args:
            pdf_path: PDF 파일 경로
            chunking_strategy: 청킹 전략 ('auto', 'toc', 'semantic', 'fixed')
            
        Returns:
            성공 여부
        """
        return self._process_single_pdf(pdf_path, chunking_strategy)
    
    def _setup_database(self, force_recreate: bool) -> bool:
        """
        데이터베이스 설정
        
        Args:
            force_recreate: 기존 컬렉션을 삭제하고 새로 생성할지 여부
            
        Returns:
            성공 여부
        """
        try:
            # Qdrant 연결 확인
            if not self.qdrant_service.health_check():
                logger.error("Qdrant 서비스에 연결할 수 없습니다.")
                return False
            
            # 컬렉션 생성
            if not self.qdrant_service.create_collection(force_recreate):
                logger.error("Qdrant 컬렉션 생성에 실패했습니다.")
                return False
            
            logger.info("데이터베이스 설정 완료")
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 설정 중 오류 발생: {str(e)}")
            return False
    
    def _process_single_pdf(self, pdf_path: Path, chunking_strategy: str = 'auto') -> bool:
        """
        단일 PDF 파일 처리 (내부 메서드)
        
        Args:
            pdf_path: PDF 파일 경로
            chunking_strategy: 청킹 전략
            
        Returns:
            성공 여부
        """
        try:
            logger.info(f"PDF 처리 시작: {pdf_path.name}")
            
            # 1. PDF에서 텍스트 추출
            pdf_data = self.pdf_processor.extract_text_from_pdf(pdf_path)
            text_content = pdf_data['text_content']
            doc_metadata = pdf_data['document_metadata']
            
            logger.info(f"텍스트 추출 완료: {len(text_content)}페이지")
            
            # 2. 목차 추출
            toc_items = self.pdf_processor.extract_table_of_contents(text_content)
            logger.info(f"목차 추출 완료: {len(toc_items)}개 항목")
            
            # 3. 청킹 전략 결정
            if chunking_strategy == 'auto':
                chunking_strategy = 'toc' if toc_items else 'semantic'
            
            # 4. 텍스트 청킹
            chunks = self._chunk_text(text_content, toc_items, chunking_strategy)
            if not chunks:
                logger.warning(f"청킹 결과가 없습니다: {pdf_path.name}")
                return False
            
            logger.info(f"텍스트 청킹 완료: {len(chunks)}개 청크")
            
            # 5. 메타데이터 추가
            chunks = self._add_metadata_to_chunks(chunks, pdf_path, doc_metadata)
            
            # 6. 임베딩 생성
            chunks_with_embeddings = self.embedding_service.batch_generate_embeddings_with_metadata(chunks)
            
            # 7. 벡터 DB에 저장
            if self.qdrant_service.insert_chunks(chunks_with_embeddings):
                self.stats['total_chunks'] += len(chunks)
                self.stats['successful_chunks'] += len(chunks)
                logger.info(f"벡터 DB 저장 완료: {pdf_path.name}")
                return True
            else:
                self.stats['failed_chunks'] += len(chunks)
                logger.error(f"벡터 DB 저장 실패: {pdf_path.name}")
                return False
                
        except Exception as e:
            logger.error(f"PDF 처리 중 오류 발생: {pdf_path.name}, 오류: {str(e)}")
            return False
    
    def _chunk_text(self, text_content: List[str], toc_items: List[Dict[str, Any]], 
                    strategy: str) -> List[Dict[str, Any]]:
        """
        텍스트 청킹
        
        Args:
            text_content: 페이지별 텍스트 리스트
            toc_items: 목차 항목 리스트
            strategy: 청킹 전략
            
        Returns:
            청킹된 텍스트 리스트
        """
        try:
            if strategy == 'toc' and toc_items:
                return self.text_chunker.chunk_by_toc(text_content, toc_items)
            elif strategy == 'semantic':
                return self.text_chunker.chunk_by_semantic(text_content)
            elif strategy == 'fixed':
                return self.text_chunker.chunk_by_fixed_size(text_content)
            else:
                # 기본값은 의미적 청킹
                return self.text_chunker.chunk_by_semantic(text_content)
                
        except Exception as e:
            logger.error(f"텍스트 청킹 중 오류 발생: {str(e)}")
            return []
    
    def _add_metadata_to_chunks(self, chunks: List[Dict[str, Any]], 
                                pdf_path: Path, doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        청크에 메타데이터 추가
        
        Args:
            chunks: 청크 리스트
            pdf_path: PDF 파일 경로
            doc_metadata: 문서 메타데이터
            
        Returns:
            메타데이터가 추가된 청크 리스트
        """
        try:
            # 언어 감지
            language = self.pdf_processor.detect_language_from_filename(pdf_path.name)
            
            for chunk in chunks:
                # 기본 메타데이터 추가
                chunk['source_file'] = str(pdf_path)
                chunk['file_name'] = pdf_path.name
                chunk['created_at'] = datetime.now().isoformat()
                
                # 기존 메타데이터에 추가 정보 병합
                if 'metadata' not in chunk:
                    chunk['metadata'] = {}
                
                chunk['metadata'].update({
                    'file_name': pdf_path.name,
                    'file_size': doc_metadata.get('file_size', 0),
                    'total_pages': doc_metadata.get('total_pages', 0),
                    'title': doc_metadata.get('title', ''),
                    'author': doc_metadata.get('author', ''),
                    'subject': doc_metadata.get('subject', ''),
                    'language': language
                })
            
            return chunks
            
        except Exception as e:
            logger.error(f"메타데이터 추가 중 오류 발생: {str(e)}")
            return chunks
    
    def _print_final_stats(self):
        """최종 통계 출력"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("=== ETL 파이프라인 통계 ===")
        logger.info(f"총 파일 수: {self.stats['total_files']}")
        logger.info(f"처리된 파일 수: {self.stats['processed_files']}")
        logger.info(f"총 청크 수: {self.stats['total_chunks']}")
        logger.info(f"성공한 청크 수: {self.stats['successful_chunks']}")
        logger.info(f"실패한 청크 수: {self.stats['failed_chunks']}")
        logger.info(f"처리 시간: {duration}")
        
        # 성공률 계산
        if self.stats['total_chunks'] > 0:
            success_rate = (self.stats['successful_chunks'] / self.stats['total_chunks']) * 100
            logger.info(f"성공률: {success_rate:.2f}%")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        파이프라인 통계 반환
        
        Returns:
            통계 정보 딕셔너리
        """
        return self.stats.copy()
    
    def search_documents(self, query: str, limit: int = 10, 
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        문서 검색
        
        Args:
            query: 검색 쿼리
            limit: 반환할 결과 수
            filters: 검색 필터
            
        Returns:
            검색 결과 리스트
        """
        try:
            return self.qdrant_service.search_by_text(query, limit, filters)
        except Exception as e:
            logger.error(f"문서 검색 중 오류 발생: {str(e)}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        컬렉션 정보 조회
        
        Returns:
            컬렉션 정보
        """
        try:
            return self.qdrant_service.get_collection_info()
        except Exception as e:
            logger.error(f"컬렉션 정보 조회 중 오류 발생: {str(e)}")
            return {}


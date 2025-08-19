"""
ETL 파이프라인 메인 클래스
PDF 처리부터 벡터 DB 저장까지 전체 과정을 조율
"""

from etl.embedding_service import EmbeddingService
from etl.pdf_chunking import PDFProcessor
import time
from loguru import logger


class ETLPipeline:
    """ETL 파이프라인 메인 클래스"""

    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.embedding_service = EmbeddingService()

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

    def run(self):
        """ETL 파이프라인 실행"""
        self.stats['start_time'] = time.time()
        logger.info("ETL 파이프라인 시작")

        try:
            # 1. PDF 로드 및 청킹
            logger.info("1단계: PDF 로드 및 청킹")
            pdfs = self.pdf_processor.load_pdfs()
            self.stats['total_files'] = len(pdfs)
            chunked_pdfs = []

            """PDF 청킹 로직"""
            for pdf in pdfs:
                chunked_pdf = self.pdf_processor.process_pdf(pdf)
                if chunked_pdf:
                    chunked_pdfs.extend(chunked_pdf)
                    self.stats['processed_files'] += 1
                    self.stats['total_chunks'] += len(chunked_pdf)
                    logger.info(f"PDF 처리 완료: {pdf} ({len(chunked_pdf)}개 청크)")
                else:
                    logger.error(f"PDF 처리 실패: {pdf}")

            if not chunked_pdfs:
                logger.warning("처리된 청크가 없습니다. ETL 파이프라인을 종료합니다.")
                return self._finalize_stats()

            logger.info(f"청킹 완료: 총 {len(chunked_pdfs)}개 청크 생성")

            # 2. 임베딩 생성 및 FAISS DB 저장
            logger.info("2단계: 임베딩 생성 및 FAISS DB 저장")
            faiss_db = self.embedding_service.create_embeddings(chunked_pdfs)

            if faiss_db is not None:
                # FAISS DB에 저장된 벡터 수 확인
                vector_count = faiss_db.index.ntotal if hasattr(faiss_db.index, 'ntotal') else len(chunked_pdfs)
                self.stats['successful_chunks'] = vector_count
                self.stats['failed_chunks'] = len(chunked_pdfs) - vector_count

                logger.info(f"임베딩 생성 및 저장 완료: {vector_count}개 벡터")
            else:
                logger.error("임베딩 생성 실패")
                self.stats['failed_chunks'] = len(chunked_pdfs)
                return self._finalize_stats()

        except Exception as e:
            logger.error(f"ETL 파이프라인 실행 중 오류 발생: {str(e)}")

        finally:
            self._finalize_stats()
            logger.info("ETL 파이프라인 완료")

        return self.stats

    def _finalize_stats(self):
        """통계 정보 최종화"""
        self.stats['end_time'] = time.time()
        if self.stats['start_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            logger.info(f"전체 처리 시간: {duration:.2f}초")
            logger.info(f"처리 통계: {self.stats}")
        return self.stats

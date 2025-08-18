#!/usr/bin/env python3
"""
ETL 파이프라인 사용 예시
"""
from pathlib import Path

from loguru import logger

from etl.etl_pipeline import ETLPipeline
from etl.utils import create_processing_report, save_processing_log


def example_basic_usage():
    """기본 사용 예시"""
    logger.info("=== 기본 ETL 파이프라인 실행 예시 ===")
    
    # ETL 파이프라인 초기화
    pipeline = ETLPipeline()
    
    # 전체 파이프라인 실행
    success = pipeline.run_full_pipeline()
    
    if success:
        logger.info("파이프라인 실행 성공!")
        
        # 통계 정보 조회
        stats = pipeline.get_pipeline_stats()
        logger.info(f"처리된 파일 수: {stats['processed_files']}")
        logger.info(f"생성된 청크 수: {stats['successful_chunks']}")
        
        # 컬렉션 정보 조회
        collection_info = pipeline.get_collection_info()
        logger.info(f"벡터 DB 컬렉션: {collection_info.get('name', 'N/A')}")
        logger.info(f"저장된 벡터 수: {collection_info.get('vectors_count', 'N/A')}")
    else:
        logger.error("파이프라인 실행 실패!")

def example_single_pdf_processing():
    """단일 PDF 처리 예시"""
    logger.info("=== 단일 PDF 처리 예시 ===")
    
    pipeline = ETLPipeline()
    
    # 특정 PDF 파일 처리
    pdf_path = Path("guidebook_pdfs/guidebook_ko.pdf")
    
    if pdf_path.exists():
        success = pipeline.process_single_pdf(pdf_path, chunking_strategy='toc')
        
        if success:
            logger.info("PDF 처리 성공!")
        else:
            logger.error("PDF 처리 실패!")
    else:
        logger.warning(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

def example_search_functionality():
    """검색 기능 예시"""
    logger.info("=== 검색 기능 예시 ===")
    
    pipeline = ETLPipeline()
    
    # 텍스트 검색
    query = "사용자 가이드"
    results = pipeline.search_documents(query, limit=5)
    
    logger.info(f"검색 쿼리: '{query}'")
    logger.info(f"검색 결과 수: {len(results)}")
    
    for i, result in enumerate(results[:3]):  # 상위 3개만 출력
        logger.info(f"결과 {i+1}:")
        logger.info(f"  점수: {result['score']:.4f}")
        logger.info(f"  내용: {result['content'][:100]}...")
        logger.info(f"  파일: {result['file_name']}")
        logger.info(f"  페이지: {result['page_range']}")

def example_custom_chunking():
    """사용자 정의 청킹 예시"""
    logger.info("=== 사용자 정의 청킹 예시 ===")
    
    pipeline = ETLPipeline()
    
    # 의미적 청킹으로 PDF 처리
    pdf_path = Path("guidebook_pdfs/guidebook_en.pdf")
    
    if pdf_path.exists():
        success = pipeline.process_single_pdf(pdf_path, chunking_strategy='semantic')
        
        if success:
            logger.info("의미적 청킹으로 PDF 처리 성공!")
        else:
            logger.error("의미적 청킹으로 PDF 처리 실패!")
    else:
        logger.warning(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

def example_with_reporting():
    """보고서 생성과 함께 실행하는 예시"""
    logger.info("=== 보고서 생성과 함께 실행하는 예시 ===")
    
    pipeline = ETLPipeline()
    
    # 파이프라인 실행
    success = pipeline.run_full_pipeline()
    
    if success:
        # 통계 수집
        stats = pipeline.get_pipeline_stats()
        collection_info = pipeline.get_collection_info()
        
        # 처리 보고서 생성
        time_stats = {
            'start_time': stats.get('start_time'),
            'end_time': stats.get('end_time'),
            'duration_seconds': (stats.get('end_time') - stats.get('start_time')).total_seconds() if stats.get('start_time') and stats.get('end_time') else 0
        }
        
        # 청크 요약 생성 (실제로는 청크 데이터가 필요)
        chunk_summary = {
            'total_chunks': stats.get('total_chunks', 0),
            'chunk_types': {'table_of_contents': stats.get('total_chunks', 0)},
            'languages': {'ko': stats.get('total_chunks', 0)},
            'file_sources': {'guidebook': stats.get('total_chunks', 0)}
        }
        
        report = create_processing_report(stats, chunk_summary, time_stats)
        
        # 보고서 저장
        report_path = Path("reports/etl_report.json")
        if save_processing_log(report, report_path):
            logger.info(f"처리 보고서 저장 완료: {report_path}")
        else:
            logger.error("처리 보고서 저장 실패!")
        
        logger.info("=== 처리 보고서 요약 ===")
        logger.info(f"총 파일 수: {report['pipeline_summary']['total_files']}")
        logger.info(f"처리된 파일 수: {report['pipeline_summary']['processed_files']}")
        logger.info(f"총 청크 수: {report['pipeline_summary']['total_chunks']}")
        logger.info(f"성공률: {report['success_rate']['files']:.2f}%")
        logger.info(f"처리 시간: {report['performance_metrics']['processing_time']['duration_formatted']}")

def main():
    """메인 함수"""
    logger.info("ETL 파이프라인 사용 예시 시작")
    
    try:
        # 1. 기본 사용 예시
        example_basic_usage()
        
        # 2. 단일 PDF 처리 예시
        example_single_pdf_processing()
        
        # 3. 검색 기능 예시
        example_search_functionality()
        
        # 4. 사용자 정의 청킹 예시
        example_custom_chunking()
        
        # 5. 보고서 생성과 함께 실행하는 예시
        example_with_reporting()
        
    except Exception as e:
        logger.error(f"예시 실행 중 오류 발생: {str(e)}")
    
    logger.info("ETL 파이프라인 사용 예시 완료")

if __name__ == "__main__":
    main()


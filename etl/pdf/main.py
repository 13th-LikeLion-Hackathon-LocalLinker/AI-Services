#!/usr/bin/env python3
"""
ETL 파이프라인 실행 스크립트
PDF 가이드북을 처리하여 Qdrant 벡터 DB에 저장
"""

import argparse
import sys
from pathlib import Path
from loguru import logger
from etl.pdf.etl_pipeline import ETLPipeline


def setup_logging():
    """로깅 설정"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/etl_pipeline.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="PDF 가이드북 ETL 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 전체 파이프라인 실행
  python -m etl.main
  
  # 기존 컬렉션 삭제 후 새로 생성
  python -m etl.main --force-recreate
  
  # 특정 청킹 전략 사용
  python -m etl.main --chunking-strategy toc
  
  # 특정 PDF 파일만 처리
  python -m etl.main --pdf-file guidebook_ko.pdf
        """
    )

    parser.add_argument(
        '--force-recreate',
        action='store_true',
        help='기존 Qdrant 컬렉션을 삭제하고 새로 생성'
    )

    parser.add_argument(
        '--chunking-strategy',
        choices=['auto', 'toc', 'semantic', 'fixed'],
        default='auto',
        help='텍스트 청킹 전략 (기본값: auto)'
    )

    parser.add_argument(
        '--pdf-file',
        type=str,
        help='처리할 특정 PDF 파일명 (전체 처리 시 생략)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='로그 레벨 (기본값: INFO)'
    )

    args = parser.parse_args()

    # 로그 레벨 설정
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=args.log_level
    )

    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "etl_pipeline.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )

    try:
        logger.info("ETL 파이프라인 시작")

        # ETL 파이프라인 초기화
        pipeline = ETLPipeline()

        # 전체 파이프라인 실행
        logger.info("전체 ETL 파이프라인 실행")
        success = pipeline.run()

        if success:
            logger.info("ETL 파이프라인 실행 완료")
            return 0
        else:
            logger.error("ETL 파이프라인 실행 실패")
            return 1

    except KeyboardInterrupt:
        logger.warning("사용자에 의해 중단됨")
        return 130
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

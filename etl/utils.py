"""
ETL 유틸리티 함수들
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import fitz  # PyMuPDF

def calculate_file_hash(file_path: Path) -> str:
    """
    파일의 MD5 해시 계산
    
    Args:
        file_path: 파일 경로
        
    Returns:
        MD5 해시 문자열
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_processing_log(log_data: Dict[str, Any], output_path: Path) -> bool:
    """
    처리 로그를 JSON 파일로 저장
    
    Args:
        log_data: 저장할 로그 데이터
        output_path: 출력 파일 경로
        
    Returns:
        저장 성공 여부
    """
    try:
        # 출력 디렉토리 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # JSON으로 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)
        
        return True
    except Exception as e:
        print(f"로그 저장 실패: {str(e)}")
        return False

def load_processing_log(log_path: Path) -> Optional[Dict[str, Any]]:
    """
    처리 로그를 JSON 파일에서 로드
    
    Args:
        log_path: 로그 파일 경로
        
    Returns:
        로드된 로그 데이터 또는 None
    """
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"로그 로드 실패: {str(e)}")
        return None

def validate_pdf_file(pdf_path: Path) -> Dict[str, Any]:
    """
    PDF 파일 유효성 검증
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        검증 결과 딕셔너리
    """
    result = {
        'is_valid': False,
        'error': None,
        'file_size': 0,
        'page_count': 0,
        'metadata': {},
        'hash': ''
    }
    
    try:
        # 파일 존재 확인
        if not pdf_path.exists():
            result['error'] = "파일이 존재하지 않습니다."
            return result
        
        # 파일 크기 확인
        file_size = pdf_path.stat().st_size
        result['file_size'] = file_size
        
        if file_size == 0:
            result['error'] = "파일이 비어있습니다."
            return result
        
        # PDF 열기 시도
        doc = fitz.open(pdf_path)
        
        # 페이지 수 확인
        page_count = len(doc)
        result['page_count'] = page_count
        
        if page_count == 0:
            result['error'] = "PDF에 페이지가 없습니다."
            doc.close()
            return result
        
        # 메타데이터 추출
        metadata = doc.metadata
        result['metadata'] = {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', '')
        }
        
        doc.close()
        
        # 파일 해시 계산
        result['hash'] = calculate_file_hash(pdf_path)
        
        # 모든 검증 통과
        result['is_valid'] = True
        return result
        
    except Exception as e:
        result['error'] = str(e)
        return result

def create_chunk_summary(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    청크 데이터 요약 정보 생성
    
    Args:
        chunks: 청크 데이터 리스트
        
    Returns:
        요약 정보 딕셔너리
    """
    if not chunks:
        return {
            'total_chunks': 0,
            'total_content_length': 0,
            'chunk_types': {},
            'languages': {},
            'file_sources': {},
            'toc_levels': {}
        }
    
    summary = {
        'total_chunks': len(chunks),
        'total_content_length': sum(len(chunk.get('content', '')) for chunk in chunks),
        'chunk_types': {},
        'languages': {},
        'file_sources': {},
        'toc_levels': {}
    }
    
    for chunk in chunks:
        # 청크 타입별 카운트
        chunk_type = chunk.get('metadata', {}).get('chunk_type', 'unknown')
        summary['chunk_types'][chunk_type] = summary['chunk_types'].get(chunk_type, 0) + 1
        
        # 언어별 카운트
        language = chunk.get('metadata', {}).get('language', 'unknown')
        summary['languages'][language] = summary['languages'].get(language, 0) + 1
        
        # 파일 소스별 카운트
        file_name = chunk.get('metadata', {}).get('file_name', 'unknown')
        summary['file_sources'][file_name] = summary['file_sources'].get(file_name, 0) + 1
        
        # TOC 레벨별 카운트
        toc_level = chunk.get('metadata', {}).get('toc_level', 0)
        summary['toc_levels'][toc_level] = summary['toc_levels'].get(toc_level, 0) + 1
    
    return summary

def format_file_size(size_bytes: int) -> str:
    """
    바이트 크기를 사람이 읽기 쉬운 형태로 변환
    
    Args:
        size_bytes: 바이트 크기
        
    Returns:
        포맷된 크기 문자열
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_processing_time_stats(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    처리 시간 통계 생성
    
    Args:
        start_time: 시작 시간
        end_time: 종료 시간
        
    Returns:
        시간 통계 딕셔너리
    """
    duration = end_time - start_time
    total_seconds = duration.total_seconds()
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    return {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': total_seconds,
        'duration_formatted': f"{hours:02d}:{minutes:02d}:{seconds:02d}",
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds
    }

def create_processing_report(pipeline_stats: Dict[str, Any], 
                           chunk_summary: Dict[str, Any],
                           time_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    전체 처리 보고서 생성
    
    Args:
        pipeline_stats: 파이프라인 통계
        chunk_summary: 청크 요약
        time_stats: 시간 통계
        
    Returns:
        처리 보고서 딕셔너리
    """
    report = {
        'report_generated_at': datetime.now().isoformat(),
        'pipeline_summary': {
            'total_files': pipeline_stats.get('total_files', 0),
            'processed_files': pipeline_stats.get('processed_files', 0),
            'total_chunks': pipeline_stats.get('total_chunks', 0),
            'successful_chunks': pipeline_stats.get('successful_chunks', 0),
            'failed_chunks': pipeline_stats.get('failed_chunks', 0)
        },
        'chunk_analysis': chunk_summary,
        'performance_metrics': {
            'processing_time': time_stats,
            'chunks_per_second': pipeline_stats.get('total_chunks', 0) / time_stats.get('duration_seconds', 1) if time_stats.get('duration_seconds', 0) > 0 else 0,
            'files_per_minute': pipeline_stats.get('processed_files', 0) / (time_stats.get('duration_seconds', 1) / 60) if time_stats.get('duration_seconds', 0) > 0 else 0
        },
        'success_rate': {
            'files': (pipeline_stats.get('processed_files', 0) / pipeline_stats.get('total_files', 1)) * 100 if pipeline_stats.get('total_files', 0) > 0 else 0,
            'chunks': (pipeline_stats.get('successful_chunks', 0) / pipeline_stats.get('total_chunks', 1)) * 100 if pipeline_stats.get('total_chunks', 0) > 0 else 0
        }
    }
    
    return report


"""
PDF 파일 처리 및 텍스트 추출
"""
import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger
from .config import config

class PDFProcessor:
    """PDF 파일 처리 클래스"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Dict[str, any]:
        """
        PDF에서 텍스트 추출
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트와 메타데이터를 포함한 딕셔너리
        """
        try:
            doc = fitz.open(pdf_path)
            text_content = []
            page_metadata = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # 텍스트 추출
                text = page.get_text()
                
                # 페이지 메타데이터
                page_info = {
                    'page_number': page_num + 1,
                    'text_length': len(text),
                    'bbox': page.rect,
                    'rotation': page.rotation
                }
                
                text_content.append(text)
                page_metadata.append(page_info)
            
            # 문서 메타데이터
            doc_metadata = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', ''),
                'total_pages': len(doc),
                'file_path': str(pdf_path),
                'file_name': pdf_path.name,
                'file_size': pdf_path.stat().st_size
            }
            
            doc.close()
            
            return {
                'text_content': text_content,
                'page_metadata': page_metadata,
                'document_metadata': doc_metadata
            }
            
        except Exception as e:
            logger.error(f"PDF 처리 중 오류 발생: {pdf_path}, 오류: {str(e)}")
            raise
    
    def detect_language_from_filename(self, filename: str) -> str:
        """
        파일명에서 언어 감지
        
        Args:
            filename: 파일명
            
        Returns:
            언어 코드 (ko, en, ja, zh, vi, uz)
        """
        filename_lower = filename.lower()
        
        if 'ko' in filename_lower or 'korean' in filename_lower:
            return 'ko'
        elif 'en' in filename_lower or 'english' in filename_lower:
            return 'en'
        elif 'ja' in filename_lower or 'japanese' in filename_lower:
            return 'ja'
        elif 'zh' in filename_lower or 'chinese' in filename_lower:
            return 'zh'
        elif 'vi' in filename_lower or 'vietnamese' in filename_lower:
            return 'vi'
        elif 'uz' in filename_lower or 'uzbek' in filename_lower:
            return 'uz'
        else:
            return 'unknown'
    
    def extract_table_of_contents(self, text_content: List[str]) -> List[Dict[str, any]]:
        """
        텍스트에서 목차 추출
        
        Args:
            text_content: 페이지별 텍스트 리스트
            
        Returns:
            목차 정보를 포함한 리스트
        """
        toc_items = []
        
        # 목차 패턴들 (여러 언어 지원)
        toc_patterns = [
            r'^\s*(\d+\.?\d*)\s*([^\n]+)',  # 1. 제목 또는 1.1 제목
            r'^\s*([IVX]+\.?\d*)\s*([^\n]+)',  # I. 제목 또는 I.1 제목
            r'^\s*([A-Z]\.?\d*)\s*([^\n]+)',  # A. 제목 또는 A.1 제목
            r'^\s*([가-힣]+)\s*([^\n]+)',  # 한글 제목
        ]
        
        for page_num, page_text in enumerate(text_content):
            lines = page_text.split('\n')
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                
                for pattern in toc_patterns:
                    match = re.match(pattern, line)
                    if match:
                        # 목차 항목으로 판단되는 경우
                        toc_item = {
                            'page_number': page_num + 1,
                            'line_number': line_num + 1,
                            'level': self._determine_toc_level(match.group(1)),
                            'number': match.group(1),
                            'title': match.group(2).strip(),
                            'full_text': line,
                            'page_text': page_text
                        }
                        toc_items.append(toc_item)
                        break
        
        return toc_items
    
    def _determine_toc_level(self, number: str) -> int:
        """
        목차 레벨 결정
        
        Args:
            number: 목차 번호
            
        Returns:
            목차 레벨 (1, 2, 3...)
        """
        if '.' in number:
            return len(number.split('.'))
        elif re.match(r'^[IVX]+$', number):
            return 1
        elif re.match(r'^[A-Z]$', number):
            return 1
        else:
            return 1
    
    def get_pdf_files(self, directory: Path = None) -> List[Path]:
        """
        디렉토리에서 PDF 파일 목록 가져오기
        
        Args:
            directory: 검색할 디렉토리 (기본값: 설정된 가이드북 디렉토리)
            
        Returns:
            PDF 파일 경로 리스트
        """
        if directory is None:
            directory = config.guidebook_dir
        
        pdf_files = []
        for file_path in directory.glob("*.pdf"):
            if file_path.suffix.lower() in self.supported_formats:
                pdf_files.append(file_path)
        
        return sorted(pdf_files)


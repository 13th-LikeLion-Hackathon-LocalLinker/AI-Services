"""
텍스트 청킹 전략 구현
"""
import re
import uuid
from typing import List, Dict, Any, Optional
from loguru import logger
from .config import config

class TextChunker:
    """텍스트 청킹 클래스"""
    
    def __init__(self):
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap
    
    def chunk_by_toc(self, text_content: List[str], toc_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        목차 기반 청킹
        
        Args:
            text_content: 페이지별 텍스트 리스트
            toc_items: 목차 항목 리스트
            
        Returns:
            청킹된 텍스트 리스트
        """
        chunks = []
        
        if not toc_items:
            logger.warning("목차가 없어 고정 크기 청킹으로 대체합니다.")
            return self.chunk_by_fixed_size(text_content)
        
        # 목차 항목들을 페이지 번호로 정렬
        sorted_toc = sorted(toc_items, key=lambda x: (x['page_number'], x['line_number']))
        
        for i, toc_item in enumerate(sorted_toc):
            current_page = toc_item['page_number'] - 1  # 0-based index
            current_line = toc_item['line_number'] - 1
            
            # 다음 목차 항목 찾기
            next_toc = sorted_toc[i + 1] if i + 1 < len(sorted_toc) else None
            
            # 현재 목차 항목의 내용 범위 결정
            start_page = current_page
            end_page = current_page
            
            if next_toc:
                end_page = next_toc['page_number'] - 1
            else:
                end_page = len(text_content) - 1
            
            # 해당 범위의 텍스트 추출
            section_text = self._extract_section_text(
                text_content, start_page, end_page, current_line
            )
            
            if section_text.strip():
                chunk = {
                    'chunk_id': str(uuid.uuid4()),
                    'content': section_text,
                    'metadata': {
                        'chunk_type': 'table_of_contents',
                        'toc_level': toc_item['level'],
                        'toc_number': toc_item['number'],
                        'toc_title': toc_item['title'],
                        'start_page': start_page + 1,
                        'end_page': end_page + 1,
                        'start_line': current_line + 1,
                        'language': self._detect_language_from_text(section_text)
                    }
                }
                chunks.append(chunk)
        
        return chunks
    
    def chunk_by_semantic(self, text_content: List[str]) -> List[Dict[str, Any]]:
        """
        의미적 청킹 (문단 단위)
        
        Args:
            text_content: 페이지별 텍스트 리스트
            
        Returns:
            청킹된 텍스트 리스트
        """
        chunks = []
        
        for page_num, page_text in enumerate(text_content):
            # 문단으로 분리 (빈 줄 기준)
            paragraphs = re.split(r'\n\s*\n', page_text.strip())
            
            for para_num, paragraph in enumerate(paragraphs):
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                
                # 문단이 너무 길면 더 작은 단위로 분할
                if len(paragraph) > self.chunk_size * 2:
                    sub_chunks = self._split_long_paragraph(paragraph)
                    for sub_num, sub_chunk in enumerate(sub_chunks):
                        chunk = {
                            'chunk_id': str(uuid.uuid4()),
                            'content': sub_chunk,
                            'metadata': {
                                'chunk_type': 'semantic',
                                'page_number': page_num + 1,
                                'paragraph_number': para_num + 1,
                                'sub_chunk_number': sub_num + 1,
                                'language': self._detect_language_from_text(sub_chunk)
                            }
                        }
                        chunks.append(chunk)
                else:
                    chunk = {
                        'chunk_id': str(uuid.uuid4()),
                        'content': paragraph,
                        'metadata': {
                            'chunk_type': 'semantic',
                            'page_number': page_num + 1,
                            'paragraph_number': para_num + 1,
                            'language': self._detect_language_from_text(paragraph)
                        }
                    }
                    chunks.append(chunk)
        
        return chunks
    
    def chunk_by_fixed_size(self, text_content: List[str]) -> List[Dict[str, Any]]:
        """
        고정 크기 청킹
        
        Args:
            text_content: 페이지별 텍스트 리스트
            
        Returns:
            청킹된 텍스트 리스트
        """
        chunks = []
        
        # 모든 텍스트를 하나로 합치기
        full_text = '\n'.join(text_content)
        
        # 고정 크기로 청킹
        start = 0
        while start < len(full_text):
            end = start + self.chunk_size
            
            # 문장 경계에서 자르기
            if end < len(full_text):
                # 다음 문장의 시작 부분까지 포함
                next_sentence = self._find_next_sentence_boundary(full_text, end)
                if next_sentence > end:
                    end = next_sentence
            
            chunk_text = full_text[start:end].strip()
            
            if chunk_text:
                # 청크가 속한 페이지 범위 찾기
                page_range = self._find_page_range_for_chunk(
                    full_text, start, end, text_content
                )
                
                chunk = {
                    'chunk_id': str(uuid.uuid4()),
                    'content': chunk_text,
                    'metadata': {
                        'chunk_type': 'fixed_size',
                        'start_char': start,
                        'end_char': end,
                        'start_page': page_range['start_page'],
                        'end_page': page_range['end_page'],
                        'language': self._detect_language_from_text(chunk_text)
                    }
                }
                chunks.append(chunk)
            
            # 겹치는 부분만큼 이동
            start = end - self.chunk_overlap
            if start >= len(full_text):
                break
        
        return chunks
    
    def _extract_section_text(self, text_content: List[str], start_page: int, end_page: int, start_line: int) -> str:
        """
        특정 범위의 텍스트 추출
        
        Args:
            text_content: 페이지별 텍스트 리스트
            start_page: 시작 페이지 (0-based)
            end_page: 끝 페이지 (0-based)
            start_line: 시작 라인 (0-based)
            
        Returns:
            추출된 텍스트
        """
        if start_page == end_page:
            # 같은 페이지인 경우
            page_text = text_content[start_page]
            lines = page_text.split('\n')
            return '\n'.join(lines[start_line:])
        else:
            # 여러 페이지인 경우
            texts = []
            
            # 시작 페이지 (시작 라인부터)
            if start_page < len(text_content):
                start_page_text = text_content[start_page]
                start_lines = start_page_text.split('\n')
                texts.append('\n'.join(start_lines[start_line:]))
            
            # 중간 페이지들
            for page_num in range(start_page + 1, end_page):
                if page_num < len(text_content):
                    texts.append(text_content[page_num])
            
            # 끝 페이지
            if end_page < len(text_content):
                texts.append(text_content[end_page])
            
            return '\n'.join(texts)
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """
        긴 문단을 더 작은 단위로 분할
        
        Args:
            paragraph: 분할할 문단
            
        Returns:
            분할된 문단 리스트
        """
        if len(paragraph) <= self.chunk_size:
            return [paragraph]
        
        chunks = []
        start = 0
        
        while start < len(paragraph):
            end = start + self.chunk_size
            
            if end < len(paragraph):
                # 문장 경계에서 자르기
                next_sentence = self._find_next_sentence_boundary(paragraph, end)
                if next_sentence > end:
                    end = next_sentence
            
            chunk_text = paragraph[start:end].strip()
            if chunk_text:
                chunks.append(chunk_text)
            
            start = end - self.chunk_overlap
            if start >= len(paragraph):
                break
        
        return chunks
    
    def _find_next_sentence_boundary(self, text: str, position: int) -> int:
        """
        다음 문장 경계 찾기
        
        Args:
            text: 전체 텍스트
            position: 현재 위치
            
        Returns:
            다음 문장 경계 위치
        """
        # 문장 끝 패턴들
        sentence_end_patterns = ['.', '!', '?', '。', '！', '？', '\n\n']
        
        for i in range(position, min(position + 100, len(text))):
            if text[i] in sentence_end_patterns:
                return i + 1
        
        return position
    
    def _find_page_range_for_chunk(self, full_text: str, start_char: int, end_char: int, text_content: List[str]) -> Dict[str, int]:
        """
        청크가 속한 페이지 범위 찾기
        
        Args:
            full_text: 전체 텍스트
            start_char: 청크 시작 문자 위치
            end_char: 청크 끝 문자 위치
            text_content: 페이지별 텍스트 리스트
            
        Returns:
            페이지 범위 정보
        """
        # 각 페이지의 시작 위치 계산
        page_positions = []
        current_pos = 0
        
        for page_text in text_content:
            page_positions.append(current_pos)
            current_pos += len(page_text) + 1  # +1 for newline
        
        # 시작 페이지 찾기
        start_page = 1
        for i, pos in enumerate(page_positions):
            if pos <= start_char:
                start_page = i + 1
            else:
                break
        
        # 끝 페이지 찾기
        end_page = start_page
        for i, pos in enumerate(page_positions):
            if pos <= end_char:
                end_page = i + 1
            else:
                break
        
        return {
            'start_page': start_page,
            'end_page': end_page
        }
    
    def _detect_language_from_text(self, text: str) -> str:
        """
        텍스트에서 언어 감지 (간단한 휴리스틱)
        
        Args:
            text: 감지할 텍스트
            
        Returns:
            언어 코드
        """
        # 한글 문자 비율
        korean_chars = len(re.findall(r'[가-힣]', text))
        # 일본어 문자 비율
        japanese_chars = len(re.findall(r'[あ-んア-ン]', text))
        # 중국어 문자 비율
        chinese_chars = len(re.findall(r'[一-龯]', text))
        # 총 문자 수
        total_chars = len(re.findall(r'[a-zA-Z가-힣あ-んア-ン一-龯]', text))
        
        if total_chars == 0:
            return 'unknown'
        
        korean_ratio = korean_chars / total_chars
        japanese_ratio = japanese_chars / total_chars
        chinese_ratio = chinese_chars / total_chars
        
        if korean_ratio > 0.3:
            return 'ko'
        elif japanese_ratio > 0.3:
            return 'ja'
        elif chinese_ratio > 0.3:
            return 'zh'
        else:
            return 'en'  # 기본값은 영어


"""
OpenAI API 설정 관리
환경변수에서 API 키와 모델 설정을 로드
"""
import os

from dotenv import load_dotenv
from loguru import logger

# .env 파일 로드
load_dotenv()

class OpenAIConfig:
    """OpenAI API 설정 클래스"""
    
    def __init__(self):
        # OpenAI API 키
        self.api_key = self._get_api_key()
        
        # 모델 설정
        self.chat_model = os.getenv("OPENAI_CHAT_MODEL")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL")
        self.top_k = int(os.getenv("TOP_K_RESULTS"))
        
        # API 설정
        self.max_tokens = int(os.getenv("MAX_TOKENS"))
        self.temperature = float(os.getenv("TEMPERATURE"))
        self.timeout = int(os.getenv("OPENAI_TIMEOUT", "30"))

        # 설정 검증
        self._validate_config()
        
    def _get_api_key(self) -> str:
        """API 키를 환경변수에서 가져오기"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            raise ValueError("OpenAI API 키가 필요합니다. OPENAI_API_KEY 환경변수를 설정해주세요.")
        return api_key
    
    def _validate_config(self):
        """설정 값 검증"""
        if self.max_tokens <= 0:
            logger.warning(f"잘못된 max_tokens 값: {self.max_tokens}. 기본값으로 설정합니다.")
            self.max_tokens = 1000
            
        if not (0.0 <= self.temperature <= 2.0):
            logger.warning(f"잘못된 temperature 값: {self.temperature}. 기본값으로 설정합니��.")
            self.temperature = 0.7
            
        if self.timeout <= 0:
            logger.warning(f"잘못된 timeout 값: {self.timeout}. 기본값으로 설정합니다.")
            self.timeout = 30
            
        logger.info(f"OpenAI 설정 로드 완료 - 모델: {self.chat_model}, 임베딩: {self.embedding_model}")
    
    def get_chat_config(self) -> dict:
        """채팅 모델 설정 반환"""
        return {
            "model": self.chat_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout
        }
    
    def get_embedding_config(self) -> dict:
        """임베딩 모델 설정 반환"""
        return {
            "model": self.embedding_model,
            "timeout": self.timeout
        }
    
    def is_configured(self) -> bool:
        """OpenAI 설정이 완료되었는지 확인"""
        return bool(self.api_key)
    
    def get_headers(self) -> dict:
        """API 요청용 헤더 반환"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }


# 전역 설정 인스턴스
openai_config = OpenAIConfig()

"""
OpenAI API 설정
"""
import os

from dotenv import load_dotenv

load_dotenv()


class OpenAIConfig:
    """OpenAI 설정 클래스"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.top_k_results = int(os.getenv("TOP_K_RESULTS", "5"))

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

    def get_chat_config(self) -> dict:
        """채팅 설정 반환"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

    def get_embedding_config(self) -> dict:
        """임베딩 설정 반환"""
        return {
            "model": self.embedding_model
        }


# 전역 설정 인스턴스
openai_config = OpenAIConfig()
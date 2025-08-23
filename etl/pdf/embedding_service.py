"""
임베딩 서비스
langchain의 OpenAI 임베딩을 사용하여 텍스트를 벡터로 변환하고 FAISS에 저장
"""
from langchain_community.vectorstores import FAISS
from loguru import logger

from etl.pdf.config import ETLConfig


class EmbeddingService:
    def __init__(self):
        self.config = ETLConfig()
        self.faiss_db = None

    def create_embeddings(self, documents):
        """
        문서에 대한 임베딩을 생성하고 FAISS DB에 저장합니다.

        Args:
            documents: 임베딩을 생성할 문서 리스트 (langchain Document 객체들)

        Returns:
            FAISS 벡터 데이터베이스 객체
        """
        try:
            logger.info(f"{len(documents)}개 문서에 대한 임베딩 생성 시작")

            # FAISS DB 생성 (임베딩 자동 생성)
            self.faiss_db = FAISS.from_documents(
                documents,
                embedding=self.config.embedding_model
            )

            logger.info("임베딩 생성 완료")

            # 로컬에 저장
            save_path = self.config.faiss_index_dir
            self.faiss_db.save_local(str(save_path))
            logger.info(f"FAISS 인덱스 저장 완료: {save_path}")

            return self.faiss_db

        except Exception as e:
            logger.error(f"임베딩 생성 중 오류 발생: {str(e)}")
            raise

    def load_existing_db(self):
        """기존에 저장된 FAISS DB를 로드합니다."""
        try:
            index_path = self.config.faiss_index_dir
            logger.info("현재 FAISS 인덱스 로드 시도 중..." + str(index_path))
            if index_path.exists():
                self.faiss_db = FAISS.load_local(
                    str(index_path),
                    self.config.embedding_model,
                    allow_dangerous_deserialization=True
                )
                logger.info("기존 FAISS 인덱스 로드 완료")
                return self.faiss_db
            else:
                logger.warning("기존 FAISS 인덱스를 찾을 수 없습니다.")
                return None
        except Exception as e:
            logger.error(f"FAISS 인덱스 로드 중 오류: {str(e)}")
            return None


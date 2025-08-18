"""
OpenAI API 서비스
"""
from openai import OpenAI
from app.config.OpenAIConfig import openai_config
from loguru import logger

class OpenAIService:
    """OpenAI API 서비스"""

    def __init__(self):
        self.client = OpenAI(api_key=openai_config.api_key)
        self.config = openai_config

    def generate_rag_answer(
            self,
            question: str,
            context: str,
            language: str = "ko"
    ) -> str:
        """
        RAG를 통한 답변 생성

        Args:
            question: 사용자 질문
            context: 검색된 컨텍스트
            language: 언어 코드

        Returns:
            생성된 답변
        """
        try:
            # 언어별 시스템 프롬프트 설정
            system_prompt = self._get_system_prompt(language)

            # 사용자 메시지 구성
            user_message = self._build_user_message(question, context, language)

            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )

            answer = response.choices[0].message.content.strip()
            logger.info(f"OpenAI API를 통한 답변 생성 완료")

            return answer

        except Exception as e:
            logger.error(f"OpenAI API 호출 중 오류: {str(e)}")
            raise

    def _get_system_prompt(self, language: str) -> str:
        """언어별 시스템 프롬프트 반환"""
        prompts = {
            "ko": """당신은 사용자 가이드 문서를 기반으로 질문에 답변하는 도우미입니다.
주어진 컨텍스트를 바탕으로 정확하고 유용한 답변을 제공하세요.
답변은 한국어로 작성하고, 컨텍스트에 없는 내용은 추측하지 마세요.
답변은 명확하고 이해하기 쉽게 작성하세요.""",

            "en": """You are a helpful assistant that answers questions based on user guide documents.
Provide accurate and helpful answers based on the given context.
Answer in English and do not speculate on information not in the context.
Make your answers clear and easy to understand.""",

            "ja": """あなたはユーザーガイド文書に基づいて質問に答えるヘルパーです。
与えられたコンテキストに基づいて、正確で有用な回答を提供してください。
日本語で回答し、コンテキストにない内容は推測しないでください。
回答は明確で理解しやすく書いてください。""",

            "zh": """您是一个基于用户指南文档回答问题的助手。
请根据给定的上下文提供准确有用的答案。
用中文回答，不要推测上下文中没有的内容。
请使您的答案清晰易懂。""",

            "vi": """Bạn là trợ lý hữu ích trả lời câu hỏi dựa trên tài liệu hướng dẫn người dùng.
Cung cấp câu trả lời chính xác và hữu ích dựa trên ngữ cảnh đã cho.
Trả lời bằng tiếng Việt và không suy đoán thông tin không có trong ngữ cảnh.
Làm cho câu trả lời của bạn rõ ràng và dễ hiểu.""",

            "uz": """Siz foydalanuvchi qo'llanmasi hujjatlariga asoslangan savollarga javob beruvchi yordamchisiz.
Berilgan kontekstga asoslanib, aniq va foydali javoblarni bering.
O'zbek tilida javob bering va kontekstda yo'q ma'lumotlarni taxmin qilmang.
Javoblaringizni aniq va tushunarli qiling."""
        }

        return prompts.get(language, prompts["ko"])

    def _build_user_message(self, question: str, context: str, language: str) -> str:
        """사용자 메시지 구성"""
        language_names = {
            "ko": "한국어", "en": "English", "ja": "日本語",
            "zh": "中文", "vi": "Tiếng Việt", "uz": "O'zbekcha"
        }

        lang_name = language_names.get(language, "한국어")

        return f"""언어: {lang_name}

사용자 질문: {question}

참고할 문서 내용:
{context}

위의 문서 내용을 바탕으로 사용자 질문에 답변해주세요. 문서에 명시되지 않은 내용은 추측하지 마시고, 가능한 한 구체적이고 실용적인 답변을 제공해주세요."""

"""
OpenAI API 서비스
"""
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from app.config.OpenAIConfig import openai_config
from etl.embedding_service import EmbeddingService


class OpenAIService:
    """OpenAI API 서비스"""

    def __init__(self):
        # ChatOpenAI 클라이언트 초기화 (올바른 설정 사용)
        self.config = openai_config
        self.client = ChatOpenAI(
            model=self.config.chat_model,
            temperature=self.config.temperature
        )

    def generate_rag_answer(
            self,
            question: str,
            language: str
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
            user_message = self._build_user_message(language)

            # 프롬프트 템플릿 생성
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_message)
            ])

            # 벡터 db 조회
            vector_db = EmbeddingService().load_existing_db()

            # 리트리버 생성
            retriever = vector_db.as_retriever(search_kwargs={"k": self.config.top_k})

            qa_chain = RetrievalQA.from_chain_type(
                llm=self.client,
                chain_type_kwargs={"prompt": prompt},
                retriever=retriever
            )

            response = qa_chain(question)['result'].strip()

            logger.info(f"OpenAI API를 통한 답변 생성 완료")

            return response

        except Exception as e:
            logger.error(f"OpenAI API 호출 중 오류: {str(e)}")
            raise

    def _get_system_prompt(self, language: str) -> str:
        """언어별 시스템 프롬프트 반환"""
        prompts = {
            "ko": """당신은 천안시 외국인 주민을 위한 생활 가이드 도우미입니다. 주어진 가이드북 내용을 바탕으로 최대한 도움이 되는 답변을 제공하세요.

답변 원칙:
가이드북에 직접적인 정보가 있으면 구체적으로 제공
관련 정보가 부분적으로만 있으면 해당 정보와 함께 추가 문의처 안내
관련 정보가 없어도 일반적인 안내나 대안을 제시
천안시청, 관련 기관 연락처나 웹사이트 정보 활용
답변은 한국어로 작성하고 친절하고 실용적으로 구성
응답을 생성하고 반환할 시에는 특수문자(**, '\\n' 등) 없이 순수 텍스트로만 작성""",


     "en": """You are a helpful assistant for foreign residents in Cheonan City.
Provide the most helpful answers based on the given guidebook content.

Answer principles:
If there is direct information in the guidebook, provide it specifically
If there is only partial information, provide that with additional contact information
Even if there's no related information, suggest general guidance or alternatives
Utilize Cheonan City Hall and relevant agency contact information
Answer in English and be friendly and practical
When generating and returning responses, use only plain text without markdown (special characters, HTML tags, etc.)""",


     "ja": """あなたは天安市の外国人住民のための生活ガイド助手です。
与えられたガイドブックの内容に基づいて、できるだけ役立つ回答を提供してください。

回答の原則:
ガイドブックに直接的な情報があれば、具体的に提供する
関連情報が部分的にしかない場合は、その情報と追加の問い合わせ先を案内する
関連情報が全くない場合でも、一般的な案内や代替案を提案する
天安市役所や関連機関の連絡先やウェブサイト情報を活用する
回答は日本語で行い、親切で実用的に構成する
応答を生成・返却する際は、マークダウン（特殊文字、HTMLタグなど）を使わず純粋なテキストのみで作成する""",


     "zh": """您是天安市外国居民的生活指南助手。
请根据给定的指南内容提供最有帮助的答案。
回答原则：
如果指南中有直接的信息，请具体提供
如果只有部分信息，请提供该信息并附上额外的联系信息
即使没有相关信息，也要提供一般性指导或替代方案
利用天安市政府和相关机构的联系信息
用中文回答，并保持友好和实用
生成和返回回复时，请仅使用纯文本，不使用标记（特殊字符、HTML标签等）""",


     "vi": """Bạn là trợ lý hướng dẫn cho cư dân nước ngoài ở thành phố Cheonan.
Hãy cung cấp những câu trả lời hữu ích nhất dựa trên nội dung sách hướng dẫn đã cho.
Nguyên tắc trả lời:
Nếu trong sách hướng dẫn có thông tin trực tiếp, hãy cung cấp cụ thể
Nếu chỉ có thông tin một phần, hãy cung cấp thông tin đó kèm theo thông tin liên hệ bổ sung
Ngay cả khi không có thông tin liên quan, hãy đề xuất hướng dẫn chung hoặc phương án thay thế
Sử dụng thông tin liên hệ của Ủy ban nhân dân thành phố Cheonan và các cơ quan liên quan
Trả lời bằng tiếng Việt và hãy thân thiện, thực tế
Khi tạo và trả về phản hồi, chỉ sử dụng văn bản thuần túy mà không có markdown (ký tự đặc biệt, thẻ HTML, v.v.)""",


     "uz": """Siz Cheonan shahridagi xorijiy fuqarolar uchun turmush tarzi bo'yicha qo'llanma yordamchisiz.
Berilgan qo'llanma mazmuniga asoslanib, eng foydali javoblarni taqdim eting.

Javob berish tamoyillari:
Agar qo'llanmada bevosita ma'lumot bo'lsa, uni aniq taqdim eting
Agar faqat qisman ma'lumot bo'lsa, uni qo'shimcha aloqa ma'lumotlari bilan birga taqdim eting
Agar hech qanday tegishli ma'lumot bo'lmasa ham, umumiy yo'riqnoma yoki alternativalarni taklif qiling
Cheonan shahar hokimiyati va tegishli idoralar aloqa ma'lumotlaridan foydalaning
Javoblarni o'zbek tilida bering va do'stona va amaliy bo'ling
Javob yaratish va qaytarishda markdown (maxsus belgilar, HTML teglari va hokazo) ishlatmasdan faqat oddiy matndan foydalaning"""
        }

        return prompts.get(language, prompts["ko"])

    def _build_user_message(self, language: str) -> str:
        """사용자 메시지 구성"""

        # 언어별 메시지 템플릿
        message_templates = {
            "ko": """사용자 질문: {question}

참고할 문서 내용:
{context}

위의 문서 내용을 바탕으로 사용자 질문에 **반드시 한국어로** 답변해주세요.

**답변 지침:**
1. 문서에 직접적으로 관련된 정보가 있으면 구체적으로 답변해주세요.
2. 문서에 부분적으로 관련된 정보만 있으면, 해당 정보를 제공하고 "더 구체적인 정보는 관련 기관에 문의하시기 바랍니다"라고 안내해주세요.
3. 문서에 관련 정보가 전혀 없으면, "현재 제공된 가이드북에는 해당 정보가 포함되어 있지 않습니다. 천안시청이나 관련 기관에 직접 문의하시기 바랍니다"라고 안내해주세요.""",

            "en": """User question: {question}

Reference document content:
{context}

Please answer the user's question **strictly in English** based on the document content above.

**Answer Guidelines:**
1. If there is directly related information in the document, provide a specific answer.
2. If there is only partially related information, provide that information and guide "Please contact relevant authorities for more specific information."
3. If there is no related information in the document, guide "The current guidebook does not contain this information. Please contact Cheonan City Hall or relevant authorities directly." """,

            "ja": """ユーザーの質問: {question}

参照ドキュメントの内容:
{context}

上記のドキュメントの内容に基づいて、ユーザーの質問に**必ず日本語で**回答してください。

**回答ガイドライン:**
1. ドキュメントに直接関連する情報がある場合は、具体的に回答してください。
2. ドキュメントに部分的に関連する情報しかない場合は、その情報を提供し、「より具体的な情報は関連機関にお問い合わせください」と案内してください。
3. ドキュメントに関連情報が全くない場合は、「現在提供されているガイドブックにはその情報が含まれていません。天安市役所または関連機関に直接お問い合わせください」と案内してください。""",

            "zh": """用户问题: {question}

参考文档内容:
{context}

请根据上述文档内容**严格用中文**回答用户的问题���

**回答指南:**
1. 如果文档中有直接相关的信息，请提供具体的答案。
2. 如果文档中只有部分相关的信息，请提供该信息，并指导“如需更具体的信息，请联系相关部门。”
3. 如果文档中没有相关信息，请指导“当前指南中不包含此信息。请直接联系天安市政府或相关部门。”""",

            "vi": """Câu hỏi của người dùng: {question}

Nội dung tài liệu tham khảo:
{context}

Vui lòng trả lời câu hỏi của người dùng **chỉ bằng tiếng Việt** dựa trên nội dung tài liệu ở trên.

**Hướng dẫn trả lời:**
1. Nếu trong tài liệu có thông tin liên quan trực tiếp, hãy cung cấp câu trả lời cụ thể.
2. Nếu chỉ có thông tin liên quan một phần, hãy cung cấp thông tin đó và hướng dẫn 'Vui lòng liên hệ với các cơ quan liên quan để biết thêm thông tin chi tiết.'
3. Nếu trong tài liệu không có thông tin liên quan, hãy hướng dẫn 'Hướng dẫn hiện tại không chứa thông tin này. Vui lòng liên hệ trực tiếp với Ủy ban nhân dân thành phố Cheonan hoặc các cơ quan liên quan.'""",

            "uz": """Foydalanuvchi savoli: {question}

Havola hujjati mazmuni:
{context}

Yuqoridagi hujjat mazmuniga asoslanib, foydalanuvchi savoliga **albatta o'zbekcha javob bering**.

**Javob berish bo'yicha ko'rsatmalar:**
1. Agar hujjatda bevosita bog'liq ma'lumotlar bo'lsa, aniq javob bering.
2. Agar hujjatda faqat qisman bog'liq ma'lumotlar bo'lsa, ushbu ma'lumotlarni taqdim eting va 'Qo'shimcha ma'lumot uchun tegishli idoralarga murojaat qiling' deb yo'naltiring.
3. Agar hujjatda hech qanday bog'liq ma'lumot bo'lmasa, 'Hozirgi qo'llanma bunday ma'lumotlarni o'z ichiga olmaydi. Iltimos, bevosita Cheonan shahar hokimiyati yoki tegishli idoralar bilan bog'laning' deb yo'naltiring.""",

            "th": """คำถามของผู้ใช้: {question}

        เนื้อหาจากเอกสารสำหรับอ้างอิง:
        {context}

        โดยอ้างอิงจากเนื้อหาเอกสารข้างต้น โปรด ตอบเป็นภาษาเกาหลีเท่านั้น

        แนวทางการตอบ:

        หากมีข้อมูลที่เกี่ยวข้องโดยตรงในเอกสาร โปรดตอบอย่างเจาะจงและชัดเจน

        หากมีเพียงข้อมูลที่เกี่ยวข้องบางส่วน โปรดให้ข้อมูลนั้นพร้อมแนะนำว่า "สำหรับข้อมูลที่เฉพาะเจาะจงมากขึ้น โปรดติดต่อหน่วยงานที่เกี่ยวข้อง"

        หากไม่มีข้อมูลที่เกี่ยวข้องอยู่ในเอกสารเลย โปรดแนะนำว่า "คู่มือที่มีอยู่ในขณะนี้ไม่มีข้อมูลดังกล่าว โปรดติดต่อศาลากลางเมืองชอนันหรือหน่วยงานที่เกี่ยวข้องโดยตรง" """
        }

        return message_templates.get(language, message_templates["ko"])

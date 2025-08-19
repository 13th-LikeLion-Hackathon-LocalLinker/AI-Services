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
Javob yaratish va qaytarishda markdown (maxsus belgilar, HTML teglari va hokazo) ishlatmasdan faqat oddiy matndan foydalaning""",
            "th": """คุณเป็นผู้ช่วยคู่มือการใช้ชีวิตสำหรับชาวต่างชาติในเมืองชอนัน โปรดให้คำตอบที่เป็นประโยชน์ที่สุดโดยอ้างอิงจากเนื้อหาในคู่มือที่ให้มา

        หลักการตอบ:
        หากในคู่มือมีข้อมูลโดยตรง โปรดระบุอย่างชัดเจน
        หากมีเพียงข้อมูลที่เกี่ยวข้องบางส่วน ให้ระบุข้อมูลนั้นพร้อมแจ้งช่องทางติดต่อเพิ่มเติม
        แม้ไม่มีข้อมูลที่เกี่ยวข้อง ก็ให้คำแนะนำทั่วไปหรือทางเลือกอื่น
        ใช้ข้อมูลการติดต่อหรือเว็บไซต์ของศาลากลางเมืองชอนันและหน่วยงานที่เกี่ยวข้อง
        ตอบเป็นภาษาไทยด้วยน้ำเสียงที่เป็นมิตรและใช้งานได้จริง
        เมื่อสร้างและส่งคำตอบ ให้ใช้ข้อความล้วนโดยไม่ใช้อักขระพิเศษ เช่น **, '\n' เป็นต้น"""
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
3. 문서에 관련 정보가 전혀 없으면, "현재 제공된 가이드북에는 해당 정보가 포함되어 있지 않습니다만,"이라고 한 후 당신이 알고 있는 내용들을 기반으로 안내해주세요.
4. 응답을 생성하고 반환할 시에는 특수문자(**, '\\n' 등) 없이 순수 텍스트로만 작성해주세요.""",

            "zh": """用户问题: {question}

参考的文档内容:
{context}

请基于上述文档内容，务必用韩语回答用户问题。

回答指引:

如果文档中有直接相关的信息，请具体作答。

如果只有部分相关信息，请先提供该信息，并提示："更具体的信息请咨询相关机构。"

如果文档中完全没有相关信息，请先说明："当前提供的指南中未包含该信息，不过，" 然后基于你已知的内容进行指引。

生成并返回回复时，请仅使用纯文本，不要包含特殊字符（**, '\n' 等）。""",

            "ja": """ユーザーの質問: {question}

参照用の文書内容:
{context}

上記の文書内容に基づき、必ず韓国語で回答してください。

回答ガイドライン:

文書に直接関連する情報がある場合は、具体的に回答してください。

部分的に関連する情報しかない場合は、その情報を提供し、あわせて「より具体的な情報は関係機関へお問い合わせください」と案内してください。

文書に関連情報が全くない場合は、まず「現在提供されているガイドブックには当該情報が含まれていませんが、」と述べ、そのうえであなたが把握している内容に基づいて案内してください。

応答を生成して返す際は、特殊文字（**, '\n' など）を含めず、プレーンテキストのみで記述してください。""",

            "uz": """Foydalanuvchi savoli: {question}

Ma'lumot uchun hujjat mazmuni:
{context}

Yuqoridagi hujjat mazmuniga tayangan holda, albatta koreys tilida javob bering.

Javob berish ko'rsatmalari:

Hujjatda to'g'ridan-to'g'ri tegishli ma'lumot bo'lsa, aniq va batafsil javob bering.

Faqat qisman tegishli ma'lumot bo'lsa, shu ma'lumotni bering va "Yanada aniqroq ma'lumot uchun tegishli tashkilotlarga murojaat qiling" deb yo'naltiring.

Hujjatda umuman tegishli ma'lumot bo'lmasa, avval "Hozir taqdim etilgan qo'llanmada ushbu ma'lumot mavjud emas, biroq," deb ayting va so'ng o'zingiz bilgan ma'lumotlarga asoslanib yo'l-yo'riq bering.

Javobni yaratib qaytarishda faqat oddiy matndan foydalaning, maxsus belgilarni (**, '\n' va boshqalar) ishlatmang.""",

            "en": """User question: {question}

Reference document content:
{context}

Based on the above document, please answer in Korean only.

Answer guidelines:

If the document contains directly related information, provide a specific answer.

If only partially related information exists, provide that and add: "For more specific information, please contact the relevant agency."

If there is no related information in the document, first say, "The currently provided guidebook does not include that information, however," and then provide guidance based on what you know.

When generating and returning the response, use plain text only without special characters (**, '\n', etc.).""",

            "vi": """Câu hỏi của người dùng: {question}

Nội dung tài liệu tham khảo:
{context}

Dựa trên nội dung tài liệu ở trên, vui lòng trả lời bằng tiếng Hàn.

Hướng dẫn trả lời:

Nếu tài liệu có thông tin liên quan trực tiếp, hãy trả lời cụ thể.

Nếu chỉ có thông tin liên quan một phần, hãy cung cấp thông tin đó và hướng dẫn thêm: "Để biết thông tin cụ thể hơn, vui lòng liên hệ cơ quan liên quan."

Nếu tài liệu hoàn toàn không có thông tin liên quan, trước hết hãy nói: "Sổ tay hiện có không bao gồm thông tin này, tuy nhiên," rồi cung cấp hướng dẫn dựa trên những gì bạn biết.

Khi tạo và gửi câu trả lời, chỉ sử dụng văn bản thuần, không dùng ký tự đặc biệt (**, '\n', v.v.).""",

            "th": """คำถามของผู้ใช้: {question}

เนื้อหาเอกสารสำหรับอ้างอิง:
{context}

โปรดอ้างอิงจากเอกสารข้างต้นและ ตอบเป็นภาษาเกาหลีเท่านั้น

แนวทางการตอบ:

หากมีข้อมูลที่เกี่ยวข้องโดยตรงในเอกสาร โปรดตอบให้ชัดเจนและเฉพาะเจาะจง

หากมีเพียงข้อมูลที่เกี่ยวข้องบางส่วน โปรดให้ข้อมูลนั้นพร้อมระบุว่า "สำหรับข้อมูลที่เจาะจงมากขึ้น โปรดติดต่อหน่วยงานที่เกี่ยวข้อง"

หากเอกสารไม่มีข้อมูลที่เกี่ยวข้องเลย โปรดระบุว่า "คู่มือที่ให้ไว้ในขณะนี้ไม่มีข้อมูลดังกล่าว อย่างไรก็ตาม," จากนั้นให้คำแนะนำต่อโดยอิงจากข้อมูลที่คุณทราบ

เมื่อจัดทำและส่งคำตอบ โปรดใช้ข้อความล้วนเท่านั้น โดยไม่ใส่อักขระพิเศษ (**, '\n' เป็นต้น)"""
        }

        return message_templates.get(language, message_templates["ko"])

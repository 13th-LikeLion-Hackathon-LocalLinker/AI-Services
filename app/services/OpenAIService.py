"""
OpenAI API 서비스
"""
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from app.config.OpenAIConfig import openai_config
from etl.pdf.embedding_service import EmbeddingService


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
            "ko": """다음은 사용자 질문과 가이드북에서 발췌한 컨텍스트입니다.
질문: {question}
컨텍스트: {context}

규칙:
1. 근거 우선: 반드시 컨텍스트에 명시된 사실만 사용합니다. 일반 지식이나 추측 금지.
2. 정합성: 정보가 여러 개면 최근 날짜와 정부/공식 기관 정보를 우선합니다.
3. 일치 판단:
   - 직접적 일치: 질문의 핵심 요소(대상, 지역, 제도명 등)가 컨텍스트에 모두 존재.
   - 부분적 일치: 핵심 요소 중 일부만 존재.
   - 불일치: 핵심 요소가 거의 없거나 모순.
4. 출력 언어/형식: 한국어로, 특수문자와 줄바꿈 없이 한 문단으로만 작성합니다.
5. 답변 정책:
   - 직접적 일치: 컨텍스트 기반으로 구체적으로 답변.
   - 부분적 일치: 확인된 정보만 제공하고 문장 끝에 더 구체적인 정보는 관련 기관에 문의하시기 바랍니다 를 반드시 포함.
   - 불일치(또는 근거가 1개 미만): 현재 제공된 가이드북에는 해당 정보가 포함되어 있지 않습니다만, 으로 시작하고 일반적 안내를 제공합니다.
6. 포함 항목(가능한 경우): 대상, 신청 방법, 필요 서류, 신청 기간, 접수 채널/링크, 문의처, 유의사항.
7. 근거 표기: 답변 마지막에 근거: 로 시작해 컨텍스트에서 인용한 1~2개의 짧은 문장을 따옴표 없이 그대로 붙입니다(줄바꿈 금지).
8. 금지 사항: 표/목록/불릿/마크다운/이모지 금지. 링크는 원문에 있을 때만 텍스트로 표시.

이제 위 규칙대로 최종 답변만 출력하세요.""",

            "zh": """以下是用户问题及其上下文的摘录。
问题：{question}
上下文：{context}

规则：
1. 证据优先排序：仅使用上下文中明确的事实。避免常识或猜测。
2. 一致性：当有多个来源可用时，优先使用最新日期和政府/官方机构信息。
3. 确定匹配：
- 直接匹配：问题的所有关键要素（例如，主题、地区、机构名称等）均包含在上下文中。
- 部分匹配：仅包含部分关键要素。
- 不一致：关键要素数量较少或不一致。
4. 输出语言/格式：使用中文，用一段话书写，避免使用特殊字符或换行符。
5. 回答策略：
- 直接匹配：根据上下文提供具体答案。
- 部分匹配：仅提供已验证的信息，并始终以“如需更多信息，请联系相关机构”结尾。 - 不一致（或依据少于一个）：当前指南未包含此类信息，但最初会提供一般性指南。6.（如果可能）请包含目标受众、申请方式、所需文件、申请截止日期、提交渠道/链接、联系方式以及任何备注。
7. 提供理由：以“提供理由：”开头，并直接从上下文中粘贴一两句简短的句子，无需引号（也无需换行）。
8. 禁止：禁止使用表格、列表、项目符号、Markdown 代码和表情符号。链接仅可在原文中存在时显示为文本。

目前，仅输出最终回复，并遵循上述规则。""",

            "ja": """以下は、ユーザーの質問とその文脈から抜粋したものです。
質問: {question}
コンテキスト: {context}

ルール：
1. 証拠の優先順位: 文脈上の明確な事実だけを使用して下さい。常識や推測は避けてください。
2.一貫性：複数のソースが利用可能な場合は、最新の日付と政府/公式機関の情報を優先します。
3. 一致するかどうか判断:
- 直接一致：質問のすべての重要な要素（トピック、地域、機関名など）がコンテキストに含まれています。
- 部分一致：コア要素の一部のみが含まれています。
- 不一致：コア要素の数が少ないか一貫性がありません。
4. 出力言語/形式: 日本語を使用し、1段落で作成し、特殊文字や改行は使用しないでください。
5. 回答戦略:
- 直接一致：コンテキストに基づいて具体的な回答を提供します。
- 部分一致：検証された情報のみを提供し、文章の最後は常に「詳細については関連機関にお問い合わせください。」で終わります。 - 矛盾（または根拠が1未満）：現在のガイドラインにはこの情報は含まれていませんが、一般的なガイドラインは最初に提供されます。 6.（可能であれば）対象読者、申請方法、必要書類、申請締切日、提出チャンネル/リンク、連絡先情報、メモを含めます。
7. 根拠の提示: 答えの終わりに「根拠の提示:」で始まり、文脈で1～2つの短い文章を引用符なしで（改行なしで）直接貼り付けます。
8.禁止：表、リスト、箇条書き、マークダウンコード、絵文字は禁止されています。リンクは、元のテキストにある場合にのみテキストとして表示できます。

現在は上記の規則に従って最終回答のみを出力してください。""",

            "uz": """Quyida foydalanuvchi savolidan va uning kontekstidan parchalar keltirilgan.
Savol: {question}
Kontekst: {context}

Qoidalar:
1. Dalillarning ustuvorligi: faqat kontekstdan aniq bo'lgan faktlardan foydalaning. Sog'lom fikr yoki taxminlardan qoching.
2. Muvofiqlik: Bir nechta manbalar mavjud bo'lganda, eng so'nggi sanalar va davlat/rasmiy agentlik ma'lumotlariga ustunlik bering.
3. Moslikni aniqlash:
- To'g'ridan-to'g'ri moslik: Savolning barcha asosiy elementlari (masalan, mavzu, mintaqa, agentlik nomi va boshqalar) kontekstga kiritilgan.
- Qisman moslik: Faqat ba'zi asosiy elementlar kiritilgan.
- Mos kelmaydigan: asosiy elementlar soni kichik yoki mos kelmaydi.
4. Chiqarish tili/formati: O‘zbek tilidan foydalaning, bitta xatboshida yozing va maxsus belgilar yoki qator uzilishlaridan saqlaning.
5. Javob strategiyasi:
- To'g'ridan-to'g'ri moslik: kontekstga asoslangan aniq javob bering.
- Qisman moslik: Faqat tasdiqlangan ma'lumotlarni taqdim eting, har doim "Qo'shimcha ma'lumot olish uchun tegishli agentlikka murojaat qiling" bilan yakunlangan jumlalar. - nomuvofiqliklar (yoki bitta asosdan kam): joriy ko'rsatmalar ushbu ma'lumotni o'z ichiga olmaydi, lekin umumiy ko'rsatmalar dastlab taqdim etiladi. 6. (Agar iloji bo'lsa) maqsadli auditoriyani, ariza berish usulini, talab qilinadigan hujjatlarni, ariza topshirishning oxirgi muddatini, yuborish kanali/havolasini, aloqa ma'lumotlarini va har qanday eslatmani kiriting.
7. Asos keltiring: Javobingizni “Ostiqlashtiring:” so‘zi bilan boshlang va bir yoki ikkita qisqa jumlani to‘g‘ridan-to‘g‘ri kontekstdan, tirnoqsiz (va qatorlarsiz) joylashtiring.
8. Taqiqlangan: jadvallar, roʻyxatlar, oʻq nuqtalari, Markdown kodi va emojilar taqiqlangan. Havolalar faqat asl matnda mavjud bo'lsa, matn sifatida ko'rsatilishi mumkin.

Hozirda yuqoridagi qoidalarga amal qilgan holda faqat yakuniy javobni chiqaring.""",

            "en": """The following is a user question and context excerpted from the guidebook.
Question: {question}
Context: {context}

Rules:
1. Prioritize evidence: Only use facts specified in the context. Avoid general knowledge or speculation.
2. Consistency: When multiple sources of information are available, the most recent date and government/official agency information are given priority.
3. Matching Decisions:
- Direct Match: All key elements of the question (e.g., subject, region, institution name, etc.) are present in the context.
- Partial Match: Only some key elements are present.
- Inconsistent: Few or contradictory key elements are present.
4. Output Language/Format: English, one paragraph only, without special characters or line breaks.
5. Response Policy:
- Direct Match: Provide a specific answer based on the context.
- Partial Match: Provide only verified information and always include "Please contact the relevant agency for more specific information" at the end of the sentence.
- Inconsistent (or with less than one basis): The information is not currently included in the guidebook, but it begins with " and provides general guidance."
6. Include (if applicable): Target audience, application method, required documents, application period, submission channel/link, contact information, and notes.
7. Base notation: At the end of your response, begin with "Base:" and include 1-2 short sentences directly from the context, without quotation marks (no line breaks).
8. Prohibited items: No tables, lists, bullets, Markdown, or emojis. Links should be displayed as text only when they appear in the original text.

Now, print only the final response, following the above rules.""",

            "vi": """Sau đây là câu hỏi và ngữ cảnh của người dùng được trích từ sách hướng dẫn.
Câu hỏi: {question}
Bối cảnh: {context}

Quy tắc:
1. Ưu tiên bằng chứng: Chỉ sử dụng các thông tin được nêu rõ ràng trong ngữ cảnh. Tránh sử dụng kiến thức chung chung hoặc phỏng đoán.
2. Nhất quán: Khi có nhiều nguồn thông tin, ngày tháng gần đây nhất và thông tin của cơ quan chính phủ/chính thức sẽ được ưu tiên.
3. Quyết định đối sánh:
- Đối sánh trực tiếp: Tất cả các yếu tố chính của câu hỏi (ví dụ: chủ đề, khu vực, tên cơ quan, v.v.) đều có trong ngữ cảnh.
- Đối sánh một phần: Chỉ một số yếu tố chính có mặt.
- Không nhất quán: Có ít hoặc không nhất quán các yếu tố chính.
4. Ngôn ngữ/Định dạng đầu ra: Tiếng Việt, chỉ một đoạn văn, không có ký tự đặc biệt hoặc ngắt dòng.
5. Chính sách trả lời:
- Đối sánh trực tiếp: Cung cấp câu trả lời cụ thể dựa trên ngữ cảnh.
- Đối sánh một phần: Chỉ cung cấp thông tin đã được xác minh và luôn bao gồm "Vui lòng liên hệ với cơ quan liên quan để biết thêm thông tin cụ thể" ở cuối câu. - Không nhất quán (hoặc ít hơn một cơ sở): Sổ tay hướng dẫn hiện tại không bao gồm thông tin này, nhưng bắt đầu bằng và cung cấp hướng dẫn chung.
6. Bao gồm (nếu có thể): Đối tượng mục tiêu, phương thức nộp hồ sơ, tài liệu cần thiết, thời hạn nộp hồ sơ, kênh/liên kết nộp hồ sơ, thông tin liên hệ và ghi chú.
7. Chỉ rõ cơ sở: Ở cuối câu trả lời, hãy bắt đầu bằng cơ sở: và dán 1-2 câu ngắn trực tiếp từ ngữ cảnh, không có dấu ngoặc kép (không ngắt dòng).
8. Các mục bị cấm: Không có bảng/danh sách/dấu đầu dòng/markdown/biểu tượng cảm xúc. Liên kết chỉ nên được hiển thị dưới dạng văn bản khi chúng xuất hiện trong văn bản gốc.

Bây giờ, chỉ xuất ra câu trả lời cuối cùng, tuân theo các quy tắc trên.""",

            "th": """ต่อไปนี้เป็นคำถามของผู้ใช้และบริบทที่ตัดตอนมาจากคู่มือ
คำถาม: {question}
บริบท: {context}

กฎ:
1. ลำดับความสำคัญของหลักฐาน: ใช้เฉพาะข้อเท็จจริงที่ระบุในบริบท หลีกเลี่ยงการคาดเดาหรือความรู้ทั่วไป
2. ความสอดคล้อง: เมื่อมีแหล่งข้อมูลหลายแหล่ง จะใช้วันที่ล่าสุดและข้อมูลรัฐบาล/หน่วยงานอย่างเป็นทางการก่อน
3. การตัดสินใจจับคู่:
- การจับคู่โดยตรง: องค์ประกอบสำคัญทั้งหมดของคำถาม (เช่น วิชา ภูมิภาค ชื่อสถาบัน ฯลฯ) ปรากฏอยู่ในบริบท
- การจับคู่บางส่วน: มีเพียงองค์ประกอบสำคัญบางส่วนเท่านั้น
- ไม่สอดคล้อง: มีองค์ประกอบสำคัญน้อยหรือไม่สอดคล้องกัน
4. ภาษา/รูปแบบผลลัพธ์: ภาษาไทย หนึ่งย่อหน้าเท่านั้น โดยไม่มีอักขระพิเศษหรือการแบ่งบรรทัด
5. นโยบายการตอบกลับ:
- การจับคู่โดยตรง: ให้คำตอบที่เฉพาะเจาะจงตามบริบท
- การจับคู่บางส่วน: ให้เฉพาะข้อมูลที่ตรวจสอบแล้ว และใส่ "กรุณาติดต่อหน่วยงานที่เกี่ยวข้องเพื่อขอข้อมูลเพิ่มเติม" ไว้ท้ายประโยคเสมอ - ความไม่สอดคล้องกัน (หรือน้อยกว่าหนึ่งเกณฑ์): คู่มือที่ให้มาในปัจจุบันไม่ได้ระบุข้อมูลนี้ แต่ขึ้นต้นด้วยและให้คำแนะนำทั่วไป
6. ระบุ (ถ้าเป็นไปได้): กลุ่มเป้าหมาย วิธีการสมัคร เอกสารประกอบการสมัคร ระยะเวลาการสมัคร ช่องทาง/ลิงก์สำหรับส่ง ข้อมูลติดต่อ และหมายเหตุ
7. ระบุเกณฑ์: ท้ายคำตอบของคุณ ให้ขึ้นต้นด้วยเกณฑ์: และวางประโยคสั้นๆ 1-2 ประโยคจากบริบทโดยตรง โดยไม่ต้องใส่เครื่องหมายคำพูด (ห้ามขึ้นบรรทัดใหม่)
8. รายการที่ห้ามใช้: ห้ามใช้ตาราง/รายการ/สัญลักษณ์แสดงหัวข้อย่อย/มาร์กดาวน์/อิโมจิ ลิงก์ควรแสดงเป็นข้อความเฉพาะเมื่อปรากฏในข้อความต้นฉบับ

จากนั้น ให้พิมพ์คำตอบสุดท้ายตามหลักเกณฑ์ข้างต้น"""
        }

        return message_templates.get(language, message_templates["ko"])

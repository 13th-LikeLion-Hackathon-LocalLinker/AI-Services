from pathlib import Path

from etl.pdf.config import ETLConfig
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PDFProcessor:
    """PDF 파일을 로드하고 처리하는 클래스"""
    @staticmethod
    def load_pdfs():
        pdf_dir = Path(ETLConfig().guidebook_dir)
        pdf_files = []

        if pdf_dir.exists():
            for file_path in pdf_dir.glob("*.pdf"):
                if file_path.is_file():
                    pdf_files.append(str(file_path))

        return pdf_files

    @staticmethod
    def process_pdf(pdf_path: str):
        """PDF 파일을 로드하고 청킹하여 반환"""

        # PDF 로드
        loader = PyPDFLoader(pdf_path)
        documents = loader.load_and_split()

        # 텍스트 청킹
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ETLConfig().chunk_size,
            chunk_overlap=ETLConfig().chunk_overlap,
            length_function=len,
        )

        chunks = text_splitter.split_documents(documents)

        return chunks


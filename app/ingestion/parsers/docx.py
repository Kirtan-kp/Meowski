from docx import Document
from app.ingestion.parsers.base import BaseParser

class DOCXParser(BaseParser):

    def parse(self , file_path : str) -> str:
        document = Document(file_path)
        paragraphs = []

        for paragraph in document.paragraphs:
            paragraphs.append(paragraph.text)

        return "\n".join(paragraphs)
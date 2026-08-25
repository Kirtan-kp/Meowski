from app.ingestion.parsers.base import BaseParser
from pypdf import PdfReader

class PDFReader(BaseParser):

    def parse(self , file_path : str) -> str:

        reader = PdfReader(file_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text() or ""  #some pages can return None instead of None
            text += page_text +  "\n"

        return text
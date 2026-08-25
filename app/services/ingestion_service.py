from app.ingestion.validators import validate_file
from app.ingestion.cleaner import clean
from app.ingestion.parsers.docx import DOCXParser
from app.ingestion.parsers.txt import TXTReader
from app.ingestion.parsers.pdf import PDFReader
from app.ingestion.chunker import TextChunker

class IngestionService:

    def __init__(self):
        self._parsers = {".pdf" : PDFReader() , ".txt" : TXTReader() , ".docx" : DOCXParser()}
        self.chunker = TextChunker()

    def ingest(self , file_path : str , file_size : int) -> str:

        extension = validate_file(file_path,file_size)
        parser = self._parsers[extension]

        text = clean(parser.parse(file_path))

        chunks = self.chunker.chunk(text)

        return chunks
from app.ingestion.validators import validate_file
from app.ingestion.cleaner import clean
from langchain_community.document_loaders import PyPDFLoader,TextLoader,Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

class IngestionService:

    def __init__(self , file_path : str , user_id : str , session_id : str):
        self.file_path = file_path
        self.user_id = user_id
        self.session_id = session_id
        self._parsers = {".pdf" : PyPDFLoader , ".txt" : TextLoader , ".docx" : Docx2txtLoader}
        self.splitter = RecursiveCharacterTextSplitter(chunk_size = 500 , chunk_overlap = 50)
        self.file_size = os.path.getsize(file_path)

    def ingest(self):

        extension = validate_file(self.file_path , self.file_size)
        loader = self._parsers[extension](self.file_path)

        docs = loader.load()

        for document in docs:
            document.page_content = clean(
                document.page_content
            )

        chunks = self.splitter.split_documents(docs)

        for chunk in chunks:
            chunk.metadata.update({"user_id" : self.user_id , "session_id" : self.session_id})
            
        return chunks
from datetime import datetime, timedelta, timezone
from app.ingestion.validators import validate_file
from app.ingestion.cleaner import clean
from langchain_community.document_loaders import PyPDFLoader,TextLoader,Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

class IngestionService:

    def __init__(self , file_path : str , user_id : str , session_id : str , file_id : str , file_hash : str , scope : str = "session"):
        self.file_path = file_path
        self.user_id = user_id
        self.session_id = session_id
        self.file_id = file_id
        self.file_hash = file_hash
        self._parsers = {".pdf" : PyPDFLoader , ".txt" : TextLoader , ".docx" : Docx2txtLoader}
        self.splitter = RecursiveCharacterTextSplitter(chunk_size = 500 , chunk_overlap = 50)
        self.file_size = os.path.getsize(file_path)
        self.scope = scope

    def ingest(self):

        extension = validate_file(self.file_path , self.file_size)
        loader = self._parsers[extension](self.file_path)

        docs = loader.load()

        for document in docs:
            document.page_content = clean(
                document.page_content
            )

        chunks = self.splitter.split_documents(docs)
        created_at = datetime.now(timezone.utc)
        expires_at = (created_at + timedelta(hours = 24) if self.scope == "session" else None)

        for chunk in chunks:
            chunk.metadata.update({"file_id" : self.file_id , "file_hash" : self.file_hash , 
                                   "scope" : self.scope , "created_at" : created_at.isoformat()})
            
            if self.scope == "session":
                chunk.metadata["user_id"] = self.user_id
                chunk.metadata["session_id"] = self.session_id
                
            if expires_at is not None:
                chunk.metadata["expires_at"] = expires_at.isoformat()
            
        return chunks
from datetime import datetime, timedelta, timezone
from app.ingestion.validators import validate_file
from app.ingestion.cleaner import clean
from langchain_community.document_loaders import PyPDFLoader,TextLoader,Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import threading
from app.core.config import settings

_parse_semaphore = threading.BoundedSemaphore(settings.parser_concurrency_limit)

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

    def _load_documents(self):
        extension = validate_file(self.file_path, self.file_size)
        if extension == ".txt":
            loader = self._parsers[extension](self.file_path, encoding="utf-8")
        else:
            loader = self._parsers[extension](self.file_path)
        return loader.load()

    def ingest(self):
        if not _parse_semaphore.acquire(timeout=settings.parser_timeout_seconds):
            raise ValueError("Document parsing capacity is temporarily busy.")

        try:
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix="document-parser") as executor:
                future = executor.submit(self._load_documents)
                try:
                    docs = future.result(timeout=settings.parser_timeout_seconds)
                except FutureTimeoutError as exc:
                    future.cancel()
                    raise ValueError("Document parsing timed out.") from exc

            total_text = 0
            for document in docs:
                document.page_content = clean(document.page_content)
                total_text += len(document.page_content)

            if total_text > settings.max_upload_text_chars:
                raise ValueError(
                    f"Document text exceeds the {settings.max_upload_text_chars} character limit."
                )

            chunks = self.splitter.split_documents(docs)
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(hours=24) if self.scope == "session" else None

            for index,chunk in enumerate(chunks):
                chunk.metadata.update({
                    "file_id": self.file_id,
                    "file_hash": self.file_hash,
                    "scope": self.scope,
                    "created_at": created_at.isoformat(),
                    "chunk_index": index
                })
                if self.scope == "session":
                    chunk.metadata["user_id"] = self.user_id
                    chunk.metadata["session_id"] = self.session_id
                if expires_at is not None:
                    chunk.metadata["expires_at"] = expires_at.isoformat()

            return chunks
        finally:
            _parse_semaphore.release()
import os
import tempfile
import uuid
from app.services.ingestion_service import IngestionService
from app.vectorstore.qdrant_store import QdrantVectorStore
from datetime import datetime, timedelta, timezone
from app.db.models import FileRecord
import hashlib
from sqlalchemy import select
from app.ingestion.validators import validate_file, MAX_FILE_SIZE
from app.services.bm25_index_service import BM25IndexService

class UploadService:

    def __init__(self , vector_store : QdrantVectorStore , db , session_service , bm25_index_service = None ,
                retrieval_cache_service=None):
        self.vector_store = vector_store
        self.db = db
        self.session_service = session_service
        self.bm25_index_service = bm25_index_service
        self.retrieval_cache_service = retrieval_cache_service

    def upload(self , file , user_id : str , session_id : str):

        self.session_service.get_session(session_id = session_id , user_id = user_id)
        suffix = os.path.splitext(file.filename)[1].lower()
        file.file.seek(0)
        file_bytes = file.file.read(MAX_FILE_SIZE + 1)

        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError("File size exceeds the 10 MB limit.")
        
        suffix = validate_file(file.filename , len(file_bytes))        
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        existing_file = self.db.execute(
            select(FileRecord).where(FileRecord.user_id == user_id , FileRecord.session_id == session_id,
                FileRecord.file_hash == file_hash , FileRecord.status == "ready")).scalar_one_or_none()

        if existing_file is not None:
            return self.vector_store.get_documents(existing_file.id)
        
        file_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(hours=24)

        file_record = FileRecord(id = file_id , user_id = user_id , session_id = session_id , filename = file.filename,
            file_hash = file_hash , scope = "session" , status = "processing" , created_at = created_at , expires_at = expires_at)
        
        self.db.add(file_record)
        self.db.commit()

        with tempfile.NamedTemporaryFile(delete = False , suffix = suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            ingestion_service = IngestionService(temp_path , user_id = user_id , session_id = session_id , file_id = file_id , file_hash = file_hash)
            chunks = ingestion_service.ingest()
            self.vector_store.add_documents(chunks)
            file_record.status = "ready"
            self.db.commit()

            if self.bm25_index_service is not None:
                self.bm25_index_service.invalidate_session(user_id = user_id , session_id = session_id)

            if self.retrieval_cache_service is not None:
                self.retrieval_cache_service.invalidate()

            return chunks
        
        except Exception:

            file_record.status = "failed"
            self.db.commit()
            raise
        
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
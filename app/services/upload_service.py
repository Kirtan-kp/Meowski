import os
import tempfile
import uuid
from app.services.ingestion_service import IngestionService
from app.vectorstore.qdrant_store import QdrantVectorStore
from datetime import datetime, timedelta, timezone
from app.db.models import FileRecord

class UploadService:

    def __init__(self , vector_store : QdrantVectorStore , db):
        self.vector_store = vector_store
        self.db = db

    def upload(self , file , user_id : str , session_id : str):

        suffix = os.path.splitext(file.filename)[1].lower()
        file_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(hours=24)

        file_record = FileRecord(id = file_id , user_id = user_id , session_id = session_id , filename = file.filename,
            scope = "session" , status = "processing" , created_at = created_at , expires_at = expires_at)
        
        self.db.add(file_record)
        self.db.commit()

        with tempfile.NamedTemporaryFile(delete = False , suffix = suffix) as temp_file:
            file.file.seek(0)
            temp_file.write(file.file.read())
            temp_path = temp_file.name

        try:
            ingestion_service = IngestionService(temp_path , user_id = user_id , session_id = session_id , file_id = file_id)
            chunks = ingestion_service.ingest()
            self.vector_store.add_documents(chunks)
            file_record.status = "ready"
            self.db.commit()

            return chunks
        
        except Exception:

            file_record.status = "failed"
            self.db.commit()
            raise
        
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
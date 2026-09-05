import os
import tempfile
from app.services.ingestion_service import IngestionService
from app.vectorstore.qdrant_store import QdrantVectorStore

class UploadService:

    def __init__(self, vector_store: QdrantVectorStore):
        self.vector_store = vector_store

    def upload(self , file , user_id : str , session_id : str):

        suffix = os.path.splitext(file.filename)[1].lower()

        with tempfile.NamedTemporaryFile(delete = False , suffix = suffix) as temp_file:
            file.file.seek(0)
            temp_file.write(file.file.read())
            temp_path = temp_file.name

        try:
            ingestion_service = IngestionService(temp_path , user_id = user_id , session_id = session_id)
            chunks = ingestion_service.ingest()
            self.vector_store.add_documents(chunks)

            return chunks

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
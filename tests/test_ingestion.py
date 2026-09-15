from app.services.ingestion_service import IngestionService
from pathlib import Path

sample_file = Path(__file__).resolve().parent.parent / "sample.txt"
service = IngestionService(str(sample_file) , user_id = "user_1" , session_id = "session_1" , 
                           file_id = "test-file-1" , file_hash = "test_hash")

chunks = service.ingest()

for chunk in chunks:
    print("\nCONTENT:")
    print(chunk.page_content)

    print("\nMETADATA:")
    print(chunk.metadata)
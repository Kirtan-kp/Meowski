from app.services.ingestion_service import IngestionService

service = IngestionService(r"C:\Users\asus\.vscode\Meowski\sample.txt" , user_id = "user_1" , session_id = "session_1" , 
                           file_id = "test-file-1" , file_hash = "test_hash")

chunks = service.ingest()

for chunk in chunks:
    print("\nCONTENT:")
    print(chunk.page_content)

    print("\nMETADATA:")
    print(chunk.metadata)
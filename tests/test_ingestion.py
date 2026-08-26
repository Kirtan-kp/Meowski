from app.services.ingestion_service import IngestionService

service = IngestionService(r"C:\Users\asus\.vscode\Meowski\sample.txt")

chunks = service.ingest()

for chunk in chunks:
    print("\nCONTENT:")
    print(chunk.page_content)

    print("\nMETADATA:")
    print(chunk.metadata)
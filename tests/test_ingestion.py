from app.services.ingestion_service import IngestionService

service = IngestionService()

chunks = service.ingest(r"C:\Users\asus\.vscode\Meowski\sample.csv",100)

print(chunks)

for chunk in chunks:
    print(f"\nChunk {chunk.chunk_index}")
    print(chunk.text)
from app.services.ingestion_service import IngestionService

service = IngestionService()

text = service.ingest(r"C:\Users\asus\.vscode\Meowski\sample.csv",100)

print(text)
import hashlib
from app.services.ingestion_service import IngestionService
from app.vectorstore.qdrant_store import QdrantVectorStore

FILE_PATH = "data/portfolio.txt"

def main():
    with open(FILE_PATH, "rb") as file:
        file_bytes = file.read()

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    file_id = f"portfolio-{file_hash}"

    vector_store = QdrantVectorStore(384)

    if vector_store.has_file(file_hash , scope = "portfolio"):
        print("Portfolio already ingested. Skipping.")
        return

    ingestion_service = IngestionService(FILE_PATH , user_id = "" , session_id = "",file_id = file_id,
                                         file_hash = file_hash , scope = "portfolio")

    chunks = ingestion_service.ingest()
    vector_store.add_documents(chunks)
    print(f"Portfolio ingestion complete: {len(chunks)} chunks")


if __name__ == "__main__":
    main()
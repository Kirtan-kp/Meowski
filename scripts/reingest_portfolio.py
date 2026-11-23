"""Replace the portfolio knowledge with the current data/portfolio.txt.

ingest_portfolio.py only ADDS a new version when the file changes, so the old text would stay searchable.
This script first removes every portfolio chunk, then ingests the file again.
Run inside the API container:  docker compose exec api python scripts/reingest_portfolio.py
Then restart the API so its in-memory keyword index is rebuilt:  docker compose restart api"""
import hashlib

from qdrant_client import models

from app.services.ingestion_service import IngestionService
from app.services.retrieval_cache_service import RetrievalCacheService
from app.vectorstore.qdrant_store import QdrantVectorStore

FILE_PATH = "data/portfolio.txt"


def main():
    with open(FILE_PATH, "rb") as file:
        file_bytes = file.read()

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    file_id = f"portfolio-{file_hash}"

    store = QdrantVectorStore(384)
    store.client.delete(
        collection_name=store.collection_name,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[models.FieldCondition(key="metadata.scope", match=models.MatchValue(value="portfolio"))]
            )
        ),
    )
    print("Removed the old portfolio chunks.")

    chunks = IngestionService(
        FILE_PATH, user_id="", session_id="", file_id=file_id, file_hash=file_hash, scope="portfolio"
    ).ingest()
    store.add_documents(chunks)
    RetrievalCacheService().invalidate()
    print(f"Portfolio re-ingested: {len(chunks)} chunks. Now run: docker compose restart api")


if __name__ == "__main__":
    main()

from app.services.embedding_service import EmbeddingService
from app.vectorstore.qdrant_store import QdrantVectorStore

embedding_service = EmbeddingService()

vector_store = QdrantVectorStore(
    embedding_dimension=384
)

texts = [
    "Kirtan built an anime face generation project.",
    "Kirtan worked on machine learning and computer vision.",
    "Kirtan developed a license plate recognition system.",
    "Kirtan enjoys playing video games."
]

vectors = embedding_service.embed_documents(texts)

chunks = []

for index, (text, vector) in enumerate(zip(texts, vectors)):

    chunks.append({
        "text": text,
        "vector": vector,
        "user_id": "user_1",
        "session_id": "session_1",
        "document_id": "document_1",
        "filename": "test.txt",
        "chunk_index": index
    })

vector_store.add_chunks(chunks)

print("Chunks inserted successfully.")
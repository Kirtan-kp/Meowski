import hashlib

from app.vectorstore.qdrant_store import QdrantVectorStore


def main():
    vector_store = QdrantVectorStore(384)

    with open("data/portfolio.txt", "rb") as file:
        file_hash = hashlib.sha256(file.read()).hexdigest()

    file_id = f"portfolio-{file_hash}"

    documents = vector_store.get_documents(file_id)

    documents = sorted(
        documents,
        key=lambda document: document.metadata.get("chunk_index", -1)
    )

    print(f"Total chunks: {len(documents)}")

    for document in documents:
        chunk_index = document.metadata.get("chunk_index")

        print(f"\n===== CHUNK {chunk_index} =====")
        print(document.page_content)


if __name__ == "__main__":
    main()
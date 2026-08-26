from langchain_core.documents import Document
from app.vectorstore.qdrant_store import QdrantVectorStore

vector_store = QdrantVectorStore(
    embedding_dimension=384
)

documents = [

    Document(
        page_content="Kirtan built an anime face generation project.",
        metadata={
            "user_id": "user_1",
            "session_id": "session_1",
            "document_id": "document_1",
            "filename": "test.txt",
            "chunk_index": 0
        }
    ),

    Document(
        page_content="Kirtan worked on machine learning and computer vision.",
        metadata={
            "user_id": "user_1",
            "session_id": "session_1",
            "document_id": "document_1",
            "filename": "test.txt",
            "chunk_index": 1
        }
    ),

    Document(
        page_content="Kirtan developed a license plate recognition system.",
        metadata={
            "user_id": "user_1",
            "session_id": "session_1",
            "document_id": "document_1",
            "filename": "test.txt",
            "chunk_index": 2
        }
    ),

    Document(
        page_content="Kirtan enjoys playing video games.",
        metadata={
            "user_id": "user_1",
            "session_id": "session_1",
            "document_id": "document_1",
            "filename": "test.txt",
            "chunk_index": 3
        }
    )
]

vector_store.add_documents(documents)

print("Documents inserted successfully.")
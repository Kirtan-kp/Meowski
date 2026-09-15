from app.retrieval.vector_retriever import create_vector_retriever
from app.retrieval.multi_query_retriever import create_multi_query_retriever
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.core.config import settings
from app.llm.providers.groq import GroqLLM

vector_store = QdrantVectorStore(embedding_dimension = 384)

retriever = create_vector_retriever(vector_store = vector_store , k = 3)

llm = GroqLLM()

multi_query_retriever = create_multi_query_retriever(retriever = retriever , llm = llm.llm)

documents = multi_query_retriever.invoke("What projects did Kirtan work on?")

for document in documents:
    print(document.page_content)
    print(document.metadata)
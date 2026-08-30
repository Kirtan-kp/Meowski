import logging
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.pipeline import create_retrieval_pipeline
from app.llm.providers.groq import GroqLLM
from app.rag.prompt import RAG_PROMPT
from app.rag.response import build_rag_response
from app.graph.graph import create_rag_graph

logger = logging.getLogger(__name__)

class ChatService:

    def __init__(self):

        self.vector_store = QdrantVectorStore(embedding_dimension = 384)
        self.llm = GroqLLM()
        self.user_filter = Filter(must = [FieldCondition(key = "metadata.user_id" , match = MatchValue(value = "user_1"))])
        self.retriever = create_retrieval_pipeline(vector_store = self.vector_store , llm = self.llm.llm , k = 10 , 
                                      top_n = 3 , search_type = "mmr" , filter = self.user_filter)
        self.rag_graph = create_rag_graph(retriever = self.retriever , llm = self.llm.llm , prompt = RAG_PROMPT)

    def generate_response(self , message : str , session_id : str) -> str:

        logger.info("Generating chat response for session %s" , session_id)

        result = self.rag_graph.invoke({"question" : message , "retry_count" : 0})

        return build_rag_response(result)
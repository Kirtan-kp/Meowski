import logging
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
        self.retriever = create_retrieval_pipeline(vector_store = self.vector_store , llm = self.llm.llm , k = 10 , 
                                      top_n = 3 , search_type = "mmr")
        self.rag_graph = create_rag_graph(retriever = self.retriever , llm = self.llm.llm , prompt = RAG_PROMPT)

    def generate_response(self , message : str , session_id : str , user_id : str) -> str:

        logger.info("Generating chat response for session %s for user %s" , session_id , user_id)

        result = self.rag_graph.invoke({"question" : message ,"user_id" : user_id , "session_id" : session_id , "retry_count" : 0} , 
                                       config = {"configurable" : {"thread_id" : f"{user_id}:{session_id}"}})

        return build_rag_response(result)
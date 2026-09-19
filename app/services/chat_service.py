import logging
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.pipeline import create_retrieval_pipeline
from app.llm.factory import create_llm
from app.rag.prompt import RAG_PROMPT
from app.rag.response import build_rag_response
from app.graph.graph import create_rag_graph
from app.services.session_service import SessionService
from langchain_core.messages import HumanMessage, AIMessage
from app.schemas.retrieval import RetrievalResponse
from app.llm.exceptions import LLMError,LLMProviderError,LLMRateLimitError,LLMTimeoutError
from app.services.bm25_index_service import BM25IndexService

logger = logging.getLogger(__name__)

class ChatService:

    def __init__(self , vector_store , session_service : SessionService , bm25_index_service: BM25IndexService):

        self.vector_store = vector_store
        self.llm = create_llm()
        self.retriever = create_retrieval_pipeline(vector_store = self.vector_store , llm = self.llm.llm , k = 10 , 
                                      top_n = 3 , search_type = "mmr" , bm25_index_service = bm25_index_service)
        self.rag_graph = create_rag_graph(retriever = self.retriever , llm = self.llm.llm , prompt = RAG_PROMPT)
        self.session_service = session_service

    def generate_response(self , message : str , session_id : str , user_id : str , request_id: str) -> RetrievalResponse:

        logger.info("request_id=%s stage=chat_start session_id=%s user_id=%s" , request_id , session_id , user_id)

        state = self.session_service.get_state(session_id = session_id , user_id = user_id)
        chat_history = []

        if state and state.get("chat_history"):
            for item in state["chat_history"]:
                if item["role"] == "user":
                    chat_history.append(HumanMessage(content = item["content"]))
                elif item["role"] == "assistant":
                    chat_history.append(AIMessage(content = item["content"]))
        try:
            result = self.rag_graph.invoke({"question" : message ,"user_id" : user_id , "session_id" : session_id , "request_id": request_id,
                                             "retry_count" : 0 , "chat_history": chat_history} , 
                                        config = {"configurable" : {"thread_id" : f"{user_id}:{session_id}"}})
            logger.info(
                "request_id=%s stage=chat_complete session_id=%s",
                request_id,
                session_id,
            )
        except LLMError:
            raise

        except TimeoutError as exc:
            raise LLMTimeoutError(
                "LLM provider request timed out"
            ) from exc

        except Exception as exc:
            logger.exception(
                "request_id=%s RAG graph failed for session %s",
                request_id,
                session_id,
            )

            raise LLMProviderError(
                "LLM provider request failed"
            ) from exc
            
        updated_history = result.get("chat_history", [])
        clean_history = []
        for item in updated_history:
            if isinstance(item , HumanMessage):
                clean_history.append({"role" : "user" , "content" : item.content})
            elif isinstance(item, AIMessage):
                clean_history.append({"role" : "assistant" , "content" : item.content})

        self.session_service.save_state(session_id = session_id , user_id = user_id , 
                                        state = {"chat_history" : clean_history})

        return build_rag_response(result)
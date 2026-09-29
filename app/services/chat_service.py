import logging
from app.rag.response import build_rag_response
from app.services.session_service import SessionService
from langchain_core.messages import HumanMessage, AIMessage
from app.schemas.retrieval import RetrievalResponse
from app.llm.exceptions import LLMError,LLMProviderError,LLMRateLimitError,LLMTimeoutError
from app.services.llm_quota_service import LLMQuotaService
from app.llm.guarded import QuotaGuardedLLM, set_llm_request_context, reset_llm_request_context
from app.services.preference_service import PreferenceService

logger = logging.getLogger(__name__)

class ChatService:

    def __init__(self , session_service : SessionService , preference_service : PreferenceService , rag_graph):

        self.session_service = session_service
        self.preference_service = preference_service
        self.rag_graph = rag_graph

    def generate_response(self , message : str , session_id : str , user_id : str , request_id: str) -> RetrievalResponse:

        logger.info("request_id=%s stage=chat_start session_id=%s" , request_id , session_id)

        state = self.session_service.get_state(session_id = session_id , user_id = user_id)
        chat_history = []

        if state and state.get("chat_history"):
            for item in state["chat_history"]:
                if item["role"] == "user":
                    chat_history.append(HumanMessage(content = item["content"]))
                elif item["role"] == "assistant":
                    chat_history.append(AIMessage(content = item["content"]))
        context_token = set_llm_request_context(user_id=user_id, session_id=session_id)
        try:
            preferences = self.preference_service.get_preferences(
                user_id=user_id,
            )

            preference_data = [
                {
                    "key": preference.key,
                    "value": preference.value,
                }
                for preference in preferences
            ]
            result = self.rag_graph.invoke({"question" : message ,"user_id" : user_id , "session_id" : session_id , "request_id": request_id,
                                             "retry_count" : 0 , "chat_history": chat_history , "preferences": preference_data} , 
                                        config = {})
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
        finally:
            reset_llm_request_context(context_token)
            
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
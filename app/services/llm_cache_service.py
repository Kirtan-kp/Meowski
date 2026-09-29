import hashlib
import json

from app.core.config import settings
from app.services.cache_service import CacheService


class LLMCacheService:

    def __init__(self):
        self.cache = CacheService()

    def _cache_key(
        self,
        question: str,
        context: str,
        chat_history,
        user_id: str,
        session_id: str,
        preferences=None,
    ) -> str:

        history = [
            {
                "type": message.type,
                "content": message.content,
            }
            for message in chat_history
        ]

        payload = {
            "version": settings.llm_cache_version,
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "persona_prompt_version": settings.persona_prompt_version,
            "user_id": user_id,
            "session_id": session_id,
            "question": question,
            "context": context,
            "chat_history": history,
            "preferences": sorted(
                ((item["key"], item["value"]) for item in (preferences or [])),
            ),
        }

        serialized = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
        )

        payload_hash = hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

        return f"cache:llm:{payload_hash}"

    def get(
        self,
        question: str,
        context: str,
        chat_history,
        user_id: str,
        session_id: str,
        preferences=None,
    ):

        key = self._cache_key(
            question=question,
            context=context,
            chat_history=chat_history,
            user_id=user_id,
            session_id=session_id,
            preferences=preferences,
        )

        return self.cache.get(key)

    def set(
        self,
        question: str,
        context: str,
        chat_history,
        user_id: str,
        session_id: str,
        answer: str,
        preferences=None,
    ):

        key = self._cache_key(
            question=question,
            context=context,
            chat_history=chat_history,
            user_id=user_id,
            session_id=session_id,
            preferences=preferences,
        )

        self.cache.set(
            key,
            answer,
            ttl_seconds=settings.llm_cache_ttl_seconds,
        )

    def delete(
        self,
        question: str,
        context: str,
        chat_history,
        user_id: str,
        session_id: str,
        preferences=None,
    ):

        key = self._cache_key(
            question=question,
            context=context,
            chat_history=chat_history,
            user_id=user_id,
            session_id=session_id,
            preferences=preferences,
        )

        self.cache.delete(key)
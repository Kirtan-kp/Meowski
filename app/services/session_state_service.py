import json

import redis

from app.core.config import settings


class SessionStateService:
    def __init__(self):
        self.redis = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True
        )

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}:state"

    def save_state(
        self,
        session_id: str,
        state: dict,
        ttl_seconds: int
    ):
        self.redis.setex(
            self._key(session_id),
            ttl_seconds,
            json.dumps(state)
        )

    def get_state(self, session_id: str):
        value = self.redis.get(self._key(session_id))

        if value is None:
            return None

        return json.loads(value)

    def delete_state(self, session_id: str):
        self.redis.delete(self._key(session_id))

    def refresh_ttl(
        self,
        session_id: str,
        ttl_seconds: int
    ):
        self.redis.expire(
            self._key(session_id),
            ttl_seconds
        )
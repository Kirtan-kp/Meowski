import json
import redis
from app.core.config import settings

class CacheService:

    def __init__(self , redis_url=None):

        self.redis = redis.Redis.from_url(redis_url or settings.redis_cache_url , decode_responses = True)

    def _json_default(self, value):
        if hasattr(value, "item"):
            return value.item()

        raise TypeError(
            f"Object of type {type(value).__name__} is not JSON serializable"
        )

    def get(self , key : str):

        value = self.redis.get(key)

        if value is None:
            return None

        return json.loads(value)

    def set(self , key : str , value , ttl_seconds : int):

        self.redis.set(key , json.dumps(value , default=self._json_default) , ex = ttl_seconds)

    def delete(self , key : str):
        self.redis.delete(key)

    def increment(self, key: str):
        return self.redis.incr(key)
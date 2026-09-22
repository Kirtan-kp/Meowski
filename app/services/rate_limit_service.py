import time
import redis
import hashlib
from app.core.config import settings

class RateLimitService:
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.redis_cache_url , decode_responses = True)

    def scoped_key(self, *parts: str) -> str:
        value = "|".join(parts)
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]

    def is_allowed(self , key : str , limit : int , window_seconds : int) -> bool:

        bucket = int(time.time() // window_seconds)
        redis_key = f"rate:{key}:{bucket}"
        count = self.redis.incr(redis_key)

        if count == 1:
            self.redis.expire(redis_key , window_seconds)

        return count <= limit
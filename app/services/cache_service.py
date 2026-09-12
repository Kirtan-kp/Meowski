import json
import redis
from app.core.config import settings

class CacheService:

    def __init__(self):

        self.redis = redis.Redis.from_url(settings.redis_url , decode_responses = True)

    def get(self , key : str):

        value = self.redis.get(key)

        if value is None:
            return None

        return json.loads(value)

    def set(self , key : str , value , ttl_seconds : int):

        self.redis.set(key , json.dumps(value) , ex = ttl_seconds)

    def delete(self , key : str):
        self.redis.delete(key)
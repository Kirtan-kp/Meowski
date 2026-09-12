from app.services.cache_service import CacheService

class FakeRedis:

    def __init__(self):
        self.data = {}

    def get(self , key):
        return self.data.get(key)

    def set(self , key , value , ex = None):
        self.data[key] = value

    def delete(self , key):
        self.data.pop(key, None)


def test_cache_set_and_get():

    cache = CacheService()
    cache.redis = FakeRedis()
    cache.set("test:key" , {"value": 123} , ttl_seconds = 60)
    assert cache.get("test:key") == {"value": 123}


def test_cache_get_missing_key():

    cache = CacheService()
    cache.redis = FakeRedis()
    assert cache.get("missing:key") is None


def test_cache_delete():

    cache = CacheService()
    cache.redis = FakeRedis()
    cache.set("test:key", {"value": 123} , ttl_seconds = 60)
    cache.delete("test:key")
    assert cache.get("test:key") is None
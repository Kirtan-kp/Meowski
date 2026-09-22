from app.services.rate_limit_service import RateLimitService

class FakeRedis:
    def __init__(self):

        self.counts = {}

    def incr(self , key):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self , key , seconds):
        pass


def test_rate_limit_allows_requests_within_limit():
    service = RateLimitService()
    service.redis = FakeRedis()

    for _ in range(3):
        assert service.is_allowed(key = "test" , limit = 3 , window_seconds = 60) is True


def test_rate_limit_blocks_requests_after_limit():
    service = RateLimitService()
    service.redis = FakeRedis()

    for _ in range(3):
        assert service.is_allowed(key = "test" , limit = 3 , window_seconds = 60) is True

    assert service.is_allowed(key = "test" , limit = 3 , window_seconds = 60) is False

def test_scoped_key_does_not_expose_identifiers():
    service = RateLimitService()
    key = service.scoped_key("user_123", "session_456")
    assert "user_123" not in key
    assert "session_456" not in key
    assert len(key) == 32

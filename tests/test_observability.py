from app.services.observability_service import (
    ObservabilityService,
)


class FakeRedis:

    def __init__(self):
        self.hashes = {}
        self.lists = {}

    def hincrby(self, key, field, value):
        self.hashes.setdefault(key, {})
        self.hashes[key][field] = (
            self.hashes[key].get(field, 0)
            + value
        )

    def hincrbyfloat(self, key, field, value):
        self.hashes.setdefault(key, {})
        self.hashes[key][field] = (
            self.hashes[key].get(field, 0)
            + value
        )

    def hgetall(self, key):
        return {
            k: str(v)
            for k, v in self.hashes.get(
                key,
                {}
            ).items()
        }

    def lpush(self, key, value):
        self.lists.setdefault(key, [])
        self.lists[key].insert(0, value)

    def ltrim(self, key, start, end):
        self.lists[key] = self.lists[key][start:end + 1]

    def lrange(self, key, start, end):
        return self.lists.get(key, [])[start:end + 1]


def test_record_request():
    redis = FakeRedis()
    service = ObservabilityService(
        redis_client=redis
    )

    service.record_request(
        request_id="request_1",
        route="/chat",
        method="POST",
        status_code=200,
        latency_ms=25.5,
        session_id="session_1",
    )

    metrics = service.get_metrics()

    assert metrics["metrics"]["requests_total"] == 1
    assert metrics["metrics"]["requests_success"] == 1
    assert metrics["metrics"]["route:POST:/chat:requests"] == 1

    assert (
        metrics["recent_requests"][0]["request_id"]
        == "request_1"
    )


def test_record_retrieval():
    redis = FakeRedis()
    service = ObservabilityService(
        redis_client=redis
    )

    service.record_retrieval(
        document_ids=["doc1", "doc2"],
        retrieval_scores=[0.5, 0.7],
        reranker_scores=[0.8, 0.9],
        latency_ms=12.5,
    )

    metrics = service.get_metrics()["metrics"]

    assert metrics["retrieval_calls"] == 1
    assert metrics["retrieved_documents"] == 2
    assert metrics["retrieval_score_total"] == 1.2
    assert metrics["reranker_score_total"] == 1.7


def test_record_llm():
    redis = FakeRedis()
    service = ObservabilityService(
        redis_client=redis
    )

    service.record_llm(
        provider="groq",
        model="test-model",
        estimated_tokens=500,
    )

    metrics = service.get_metrics()["metrics"]

    assert metrics["llm_calls"] == 1
    assert metrics["llm_estimated_tokens"] == 500
    assert metrics["llm_provider:groq:calls"] == 1
import json
import time
from datetime import datetime, timezone

import redis

from app.core.config import settings


class ObservabilityService:

    COUNTERS_KEY = "observability:counters"
    RECENT_REQUESTS_KEY = "observability:recent_requests"

    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis.from_url(
            settings.redis_cache_url,
            decode_responses=True,
        )

    def increment(self, metric: str, value: int = 1):
        self.redis.hincrby(
            self.COUNTERS_KEY,
            metric,
            value,
        )

    def observe_latency(self, route: str, latency_ms: float):
        self.redis.hincrby(
            self.COUNTERS_KEY,
            "requests_total",
            0,
        )

        self.redis.hincrbyfloat(
            self.COUNTERS_KEY,
            f"latency_ms_total:{route}",
            latency_ms,
        )

    def record_request(
        self,
        *,
        request_id: str,
        route: str,
        method: str,
        status_code: int,
        latency_ms: float,
        session_id: str | None = None,
        error_category: str | None = None,
    ):
        self.increment("requests_total")

        if 200 <= status_code < 400:
            self.increment("requests_success")
        else:
            self.increment("requests_errors")

        self.increment(f"route:{method}:{route}:requests")

        if status_code == 429:
            self.increment("rate_limited_requests")

        if status_code >= 500:
            self.increment("server_errors")

        self.observe_latency(route, latency_ms)

        record = {
            "request_id": request_id,
            "route": route,
            "method": method,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 2),
            "session_id": session_id,
            "error_category": error_category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.redis.lpush(
            self.RECENT_REQUESTS_KEY,
            json.dumps(record),
        )

        self.redis.ltrim(
            self.RECENT_REQUESTS_KEY,
            0,
            99,
        )

    def record_retrieval(
        self,
        *,
        document_ids: list[str],
        retrieval_scores: list[float],
        reranker_scores: list[float],
        latency_ms: float,
    ):
        self.increment("retrieval_calls")
        self.increment(
            "retrieved_documents",
            len(document_ids),
        )

        if document_ids:
            self.increment(
                "retrieval_documents_with_ids",
                len(document_ids),
            )

        self.redis.hincrbyfloat(
            self.COUNTERS_KEY,
            "retrieval_latency_ms_total",
            latency_ms,
        )

        if retrieval_scores:
            self.redis.hincrbyfloat(
                self.COUNTERS_KEY,
                "retrieval_score_total",
                round(sum(retrieval_scores), 6),
            )

        if reranker_scores:
            self.redis.hincrbyfloat(
                self.COUNTERS_KEY,
                "reranker_score_total",
                round(sum(reranker_scores), 6),
            )

    def record_llm(
        self,
        *,
        provider: str,
        model: str,
        estimated_tokens: int,
        cache_hit: bool = False,
    ):
        self.increment("llm_calls")
        self.increment(
            "llm_estimated_tokens",
            estimated_tokens,
        )

        self.increment(
            f"llm_provider:{provider}:calls"
        )

        self.increment(
            f"llm_model:{model}:calls"
        )

        if cache_hit:
            self.increment("llm_cache_hits")

    def record_quota(
        self,
        outcome: str,
    ):
        self.increment(f"quota:{outcome}")

    def get_metrics(self) -> dict:

        raw = self.redis.hgetall(
            self.COUNTERS_KEY
        )

        metrics = {}

        for key, value in raw.items():
            try:
                if "." in value:
                    metrics[key] = round(float(value), 6)
                else:
                    metrics[key] = int(value)
            except (ValueError, TypeError):
                metrics[key] = value

        recent = self.redis.lrange(
            self.RECENT_REQUESTS_KEY,
            0,
            19,
        )

        recent_requests = []

        for item in recent:
            try:
                recent_requests.append(
                    json.loads(item)
                )
            except json.JSONDecodeError:
                continue

        return {
            "metrics": metrics,
            "recent_requests": recent_requests,
        }
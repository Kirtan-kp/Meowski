import math
import time
import uuid
from datetime import datetime, timezone
import logging
import hashlib

import redis
import tiktoken

from app.core.config import settings
from app.llm.exceptions import LLMQuotaExceededError, LLMProviderDisabledError, LLMConcurrencyLimitError

logger = logging.getLogger(__name__)


class LLMQuotaService:
    """Application-level token budget guard for zero-cost LLM usage."""

    RESERVE_SCRIPT = """
    local daily = tonumber(redis.call('GET', KEYS[1]) or '0')
    local provider_daily = tonumber(redis.call('GET', KEYS[2]) or '0')
    local session_daily = tonumber(redis.call('GET', KEYS[3]) or '0')

    redis.call('ZREMRANGEBYSCORE', KEYS[4], 0, ARGV[1] - ARGV[4])
    local rolling = 0
    local entries = redis.call('ZRANGE', KEYS[4], 0, -1)
    for _, entry in ipairs(entries) do
        local separator = string.find(entry, '|', 1, true)
        if separator then
            rolling = rolling + tonumber(string.sub(entry, separator + 1))
        end
    end

    local requested = tonumber(ARGV[2])
    if daily + requested > tonumber(ARGV[5]) then return 0 end
    if provider_daily + requested > tonumber(ARGV[6]) then return 0 end
    if session_daily + requested > tonumber(ARGV[7]) then return 0 end
    if rolling + requested > tonumber(ARGV[8]) then return 0 end

    redis.call('INCRBY', KEYS[1], requested)
    redis.call('INCRBY', KEYS[2], requested)
    redis.call('INCRBY', KEYS[3], requested)

    local member = ARGV[3] .. '|' .. requested
    redis.call('ZADD', KEYS[4], ARGV[1], member)

    redis.call('EXPIRE', KEYS[1], 172800)
    redis.call('EXPIRE', KEYS[2], 172800)
    redis.call('EXPIRE', KEYS[3], 172800)
    redis.call('EXPIRE', KEYS[4], ARGV[4] * 2)

    return 1
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis.from_url(
            settings.redis_cache_url, decode_responses=True
        )
        self._encoder = None

    def _get_encoder(self):
        if self._encoder is None:
            try:
                self._encoder = tiktoken.encoding_for_model(settings.llm_model)
            except KeyError:
                self._encoder = tiktoken.get_encoding("cl100k_base")
        return self._encoder

    def estimate_tokens(self, value) -> int:
        """Estimate tokens for strings, messages, dicts, and LangChain prompt values."""
        if value is None:
            return 0

        if isinstance(value, str):
            try:
                return len(self._get_encoder().encode(value))
            except Exception:
                return max(1, math.ceil(len(value) / 4))

        if hasattr(value, "content"):
            return self.estimate_tokens(value.content) + 4

        if isinstance(value, dict):
            return sum(self.estimate_tokens(k) + self.estimate_tokens(v) for k, v in value.items())

        if isinstance(value, (list, tuple)):
            return sum(self.estimate_tokens(item) for item in value)

        return self.estimate_tokens(str(value))

    def estimate_request_tokens(self, prompt) -> int:
        input_tokens = self.estimate_tokens(prompt)
        estimated = math.ceil(
            (input_tokens + settings.llm_max_output_tokens)
            * settings.llm_token_estimate_safety_factor
        )
        return max(1, estimated)

    def _keys(self, user_id: str, session_id: str, provider: str):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        scope = hashlib.sha256(provider.encode("utf-8")).hexdigest()[:16]
        user_key = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:24]
        session_key = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24]
        return (
            f"quota:llm:daily:{scope}:{today}",
            f"quota:llm:provider:{scope}:{today}",
            f"quota:llm:session:{scope}:{user_key}:{session_key}:{today}",
            f"quota:llm:rolling:{scope}",
        )

    def acquire_concurrency(self, provider: str | None = None) -> str:
        provider = provider or settings.llm_provider
        scope = hashlib.sha256(provider.encode("utf-8")).hexdigest()[:16]
        key = f"quota:llm:concurrency:{scope}"
        count = self.redis.incr(key)
        self.redis.expire(key, settings.llm_timeout_seconds + 5)

        if count > settings.llm_concurrency_limit:
            self.redis.decr(key)
            raise LLMConcurrencyLimitError(
                "LLM capacity is busy. Please try again shortly."
            )

        return key

    def release_concurrency(self, key: str):
        self.redis.decr(key)

    def reserve(
        self,
        prompt,
        *,
        user_id: str,
        session_id: str,
        provider: str | None = None,
    ) -> int:
        provider = provider or settings.llm_provider

        if not settings.llm_provider_enabled:
            raise LLMProviderDisabledError("LLM provider is disabled by application policy")

        estimated_tokens = self.estimate_request_tokens(prompt)

        if estimated_tokens > settings.llm_max_request_tokens:
            raise LLMQuotaExceededError(
                "This request exceeds the application LLM token budget."
            )

        now = time.time()
        keys = self._keys(user_id, session_id, provider)
        member_id = uuid.uuid4().hex

        allowed = self.redis.eval(
            self.RESERVE_SCRIPT,
            4,
            *keys,
            now,
            estimated_tokens,
            member_id,
            settings.llm_rolling_window_seconds,
            settings.llm_daily_token_budget,
            settings.llm_provider_daily_token_budget,
            settings.llm_session_daily_token_budget,
            settings.llm_rolling_token_budget,
        )

        if not allowed:
            logger.warning(
                "stage=llm_quota outcome=blocked provider=%s user_id=%s session_id=%s estimated_tokens=%s",
                provider, user_id, session_id, estimated_tokens,
            )
            from app.api.dependencies import get_observability_service
            get_observability_service().record_quota(
                "blocked"
            )
            raise LLMQuotaExceededError(
                "LLM capacity is temporarily exhausted. Please try again later."
            )

        logger.info(
            "stage=llm_quota outcome=reserved provider=%s user_id=%s session_id=%s estimated_tokens=%s",
            provider, user_id, session_id, estimated_tokens,
        )
        from app.api.dependencies import get_observability_service

        get_observability_service().record_quota(
            "reserved"
        )
        return estimated_tokens

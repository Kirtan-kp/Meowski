import math
import time
import uuid
from datetime import datetime, timedelta, timezone
import logging
import hashlib

import redis
import tiktoken

from app.core.config import settings
from app.llm.exceptions import LLMQuotaExceededError, LLMProviderDisabledError, LLMConcurrencyLimitError

logger = logging.getLogger(__name__)


class Reservation(int):
    """The reserved token count (so it still behaves like a plain int) plus what is needed to settle it later."""

    def __new__(cls, tokens: int, keys=(), member_id: str = "", score: float = 0.0):
        obj = super().__new__(cls, tokens)
        obj.keys = tuple(keys)
        obj.member_id = member_id
        obj.score = score
        return obj


class LLMQuotaService:
    """Application-level token budget guard for zero-cost LLM usage."""

    # Returns {1, 0, "0"} when the reservation is granted, or {0, reason, oldest} when it is blocked.
    # reason: 2 global daily, 3 provider daily, 4 session daily, 5 global rolling, 6 session rolling.
    # oldest is the score (timestamp) of the oldest entry in the blocking rolling window, used to tell the visitor when to retry.
    RESERVE_SCRIPT = """
    local function rolling_total(key, now, window)
        redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
        local total = 0
        for _, entry in ipairs(redis.call('ZRANGE', key, 0, -1)) do
            local separator = string.find(entry, '|', 1, true)
            if separator then
                total = total + tonumber(string.sub(entry, separator + 1))
            end
        end
        return total
    end

    local function oldest(key)
        local first = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
        if first[2] then return first[2] end
        return '0'
    end

    local now = tonumber(ARGV[1])
    local requested = tonumber(ARGV[2])
    local window = tonumber(ARGV[4])

    local daily = tonumber(redis.call('GET', KEYS[1]) or '0')
    local provider_daily = tonumber(redis.call('GET', KEYS[2]) or '0')
    local session_daily = tonumber(redis.call('GET', KEYS[3]) or '0')
    local rolling = rolling_total(KEYS[4], now, window)
    local session_rolling = rolling_total(KEYS[5], now, window)

    if daily + requested > tonumber(ARGV[5]) then return {0, 2, '0'} end
    if provider_daily + requested > tonumber(ARGV[6]) then return {0, 3, '0'} end
    if session_daily + requested > tonumber(ARGV[7]) then return {0, 4, '0'} end
    if rolling + requested > tonumber(ARGV[8]) then return {0, 5, oldest(KEYS[4])} end
    if session_rolling + requested > tonumber(ARGV[9]) then return {0, 6, oldest(KEYS[5])} end

    redis.call('INCRBY', KEYS[1], requested)
    redis.call('INCRBY', KEYS[2], requested)
    redis.call('INCRBY', KEYS[3], requested)

    local member = ARGV[3] .. '|' .. requested
    redis.call('ZADD', KEYS[4], ARGV[1], member)
    redis.call('ZADD', KEYS[5], ARGV[1], member)

    redis.call('EXPIRE', KEYS[1], 172800)
    redis.call('EXPIRE', KEYS[2], 172800)
    redis.call('EXPIRE', KEYS[3], 172800)
    redis.call('EXPIRE', KEYS[4], window * 2)
    redis.call('EXPIRE', KEYS[5], window * 2)

    return {1, 0, '0'}
    """

    # After the provider answers, swap the worst-case reservation for the real token count (both directions),
    # in the three counters and in both rolling windows. KEYS match RESERVE_SCRIPT.
    SETTLE_SCRIPT = """
    local diff = tonumber(ARGV[4])
    for i = 1, 3 do
        local value = redis.call('INCRBY', KEYS[i], diff)
        if value < 0 then redis.call('DECRBY', KEYS[i], value) end
    end
    for i = 4, 5 do
        if redis.call('ZREM', KEYS[i], ARGV[1]) == 1 then
            redis.call('ZADD', KEYS[i], ARGV[3], ARGV[2])
        end
    end
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
        # Daily and rolling application budgets are intentionally global across
        # providers so a fallback provider cannot multiply the application's
        # external inference allowance. Provider-specific accounting remains
        # separate for provider caps and diagnostics.
        return (
            f"quota:llm:daily:{today}",
            f"quota:llm:provider:{scope}:{today}",
            f"quota:llm:session:{user_key}:{session_key}:{today}",
            "quota:llm:rolling",
            f"quota:llm:rolling:session:{user_key}:{session_key}",
        )

    def get_usage(self, user_id: str, session_id: str, provider: str | None = None) -> dict:
        """Read-only view of what this visitor can still ask, for the chat's energy meter.

        Looks at every budget that could block them and reports the tightest one, converted to a rough
        number of questions using the average size of their own recent requests."""
        provider = provider or settings.llm_provider
        now = time.time()
        window = settings.llm_rolling_window_seconds
        daily_key, provider_key, session_key, rolling_key, session_rolling_key = self._keys(user_id, session_id, provider)

        def spent(key):
            return int(self.redis.get(key) or 0)

        def recent(key):  # [(tokens, timestamp)] inside the rolling window, oldest first
            entries = self.redis.zrangebyscore(key, now - window, "+inf", withscores=True)
            return [(int(str(member).rsplit("|", 1)[-1]), float(score)) for member, score in entries]

        rolling, session_rolling = recent(rolling_key), recent(session_rolling_key)
        budgets = [  # (reason, limit, used, oldest entry in the window)
            (2, settings.llm_daily_token_budget, spent(daily_key), None),
            (3, settings.llm_provider_daily_token_budget, spent(provider_key), None),
            (4, settings.llm_session_daily_token_budget, spent(session_key), None),
            (5, settings.llm_rolling_token_budget, sum(t for t, _ in rolling), rolling[0][1] if rolling else None),
            (6, settings.llm_session_rolling_token_budget, sum(t for t, _ in session_rolling), session_rolling[0][1] if session_rolling else None),
        ]
        reason, limit, used, oldest = min(budgets, key=lambda b: b[1] - b[2])
        remaining = max(0, limit - used)
        own = [t for t, _ in session_rolling][-5:]
        cost = max(1, int(sum(own) / len(own)) if own else settings.usage_default_question_tokens)
        questions_left = remaining // cost

        resets_in = None
        if questions_left == 0 and (reason in (2, 3, 4) or oldest is not None):
            resets_in = self._retry_after(reason, oldest, now)

        names = {2: "daily", 3: "provider_daily", 4: "session_daily", 5: "hourly", 6: "session_hourly"}
        return {
            "questions_left": questions_left,
            "fraction": round(remaining / limit, 3) if limit > 0 else 0.0,
            "resets_in": resets_in,
            "limited_by": names[reason],
        }

    @staticmethod
    def _parse_result(result):
        """The script returns {granted, reason, oldest}; a plain 1/0 is also accepted."""
        if isinstance(result, (list, tuple)):
            return int(result[0]) == 1, int(result[1]) if len(result) > 1 else 0, result[2] if len(result) > 2 else "0"
        return result == 1, 0, "0"

    @staticmethod
    def _retry_after(reason: int, oldest, now: float) -> int | None:
        """Seconds until the blocking budget frees up (None when unknown)."""
        if reason in (2, 3, 4):  # daily budgets reset at UTC midnight
            tomorrow = (datetime.fromtimestamp(now, timezone.utc) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            return max(1, int((tomorrow - datetime.fromtimestamp(now, timezone.utc)).total_seconds()))
        if reason in (5, 6):  # rolling windows free up as old requests age out
            try:
                freed_at = float(oldest) + settings.llm_rolling_window_seconds
            except (TypeError, ValueError):
                return None
            return min(settings.llm_rolling_window_seconds, max(1, math.ceil(freed_at - now)))
        return None

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
        if self.redis.decr(key) < 0:
            self.redis.incr(key)   # key expired before release; never let the counter go negative

    def reserve(
        self,
        prompt,
        *,
        user_id: str,
        session_id: str,
        provider: str | None = None,
    ) -> int:
        provider = provider or settings.llm_provider

        if not settings.is_provider_enabled(provider):
            raise LLMProviderDisabledError(
                f"LLM provider '{provider}' is disabled by application policy"
            )

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
            5,
            *keys,
            now,
            estimated_tokens,
            member_id,
            settings.llm_rolling_window_seconds,
            settings.llm_daily_token_budget,
            settings.llm_provider_daily_token_budget,
            settings.llm_session_daily_token_budget,
            settings.llm_rolling_token_budget,
            settings.llm_session_rolling_token_budget,
        )
        granted, reason, oldest = self._parse_result(allowed)

        if not granted:
            logger.warning(
                "stage=llm_quota outcome=blocked provider=%s session_id=%s estimated_tokens=%s",
                provider, session_id, estimated_tokens,
            )
            from app.api.dependencies import get_observability_service
            get_observability_service().record_quota(
                "blocked"
            )
            raise LLMQuotaExceededError(
                "LLM capacity is temporarily exhausted. Please try again later.",
                retry_after=self._retry_after(reason, oldest, now),
            )

        logger.info(
            "stage=llm_quota outcome=reserved provider=%s session_id=%s estimated_tokens=%s",
            provider, session_id, estimated_tokens,
        )
        from app.api.dependencies import get_observability_service

        get_observability_service().record_quota(
            "reserved"
        )
        return Reservation(estimated_tokens, keys=keys, member_id=member_id, score=now)

    def settle(self, reservation, actual_tokens) -> None:
        """Replace the estimate with what the provider really used, so budgets track real spend.
        Pass 0 when the call failed (nothing was generated). Never raises: accounting must not break an answer."""
        if not isinstance(reservation, Reservation) or actual_tokens is None:
            return
        actual = max(1, int(actual_tokens))
        diff = actual - int(reservation)
        if diff == 0:
            return
        try:
            self.redis.eval(
                self.SETTLE_SCRIPT,
                5,
                *reservation.keys,
                f"{reservation.member_id}|{int(reservation)}",
                f"{reservation.member_id}|{actual}",
                reservation.score,
                diff,
            )
        except Exception:
            logger.warning("stage=llm_quota outcome=settle_failed", exc_info=True)

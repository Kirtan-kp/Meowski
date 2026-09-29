# Threat model

| Threat | Control |
|---|---|
| Prompt flooding | Edge controls when deployed + API rate limits + session quotas |
| Provider exhaustion | Request estimate + daily/rolling/session/provider budgets + concurrency cap |
| Cross-session retrieval | Mandatory Qdrant metadata filters + runtime filter verification |
| Malicious uploads | Type allowlist, byte limits, page/text limits, archive checks, bounded parser process |
| Prompt injection in documents | Retrieved content is explicitly untrusted and cannot override system policy |
| Cache poisoning | Versioned keys with query/filter/model/session context |
| Resource exhaustion | Parser/LLM concurrency limits and request/upload bounds |
| Provider failure | Provider abstraction + circuit breaker + optional fallback |
| Secret exposure | Server-side environment configuration; no provider keys in frontend |
| Sensitive logs | Request IDs and operational metadata; avoid logging prompts/files/tokens |

## Deployment boundary

Cloudflare or an equivalent trusted edge should sit in front of FastAPI for public deployment. If a reverse proxy is used, only trusted proxy headers should be accepted for client-IP rate limiting.

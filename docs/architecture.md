# Architecture

## Request path

1. Client calls FastAPI.
2. Request/session/rate-limit controls run before expensive work.
3. Session state and explicit saved preferences are loaded.
4. The query is retrieved against portfolio and current-session knowledge using dense and BM25 retrieval.
5. RRF combines rankings; the reranker selects the final evidence.
6. Session/user metadata filtering is enforced before context assembly.
7. Context includes document, page/section and chunk metadata for citation mapping.
8. The provider router applies application-side quota and concurrency guards.
9. The persona controls tone only; retrieved evidence remains the factual source of truth.

## Data boundaries

- Portfolio vectors: persistent and application-wide.
- Session vectors: temporary and scoped by user/session/file.
- Conversation state: Redis with server-side TTL.
- Session/file lifecycle metadata: PostgreSQL.
- Retrieval/LLM caches: Redis with versioned keys and session-aware keys.

## Lifecycle

Active session requests extend the configured session TTL. Session expiry deletes Redis state, marks session data expired, removes temporary Qdrant vectors, invalidates BM25 indexes, and invalidates retrieval caches.

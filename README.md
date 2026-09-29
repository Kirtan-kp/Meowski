# 🐱 Cat RAG — Secure Multi-Tenant RAG Assistant

A production-style, portfolio-integrated RAG backend that combines **hybrid retrieval, session-isolated document RAG, local embeddings, cross-encoder reranking, provider abstraction, application-level cost controls, caching, and security guardrails**.

The system is designed around a strict **zero mandatory spend** requirement and can serve as a standalone API backend for a portfolio website or other client applications.

---

## ✨ Features

- **Portfolio RAG** — persistent knowledge base containing portfolio/project information.
- **Temporary Document RAG** — visitors can upload supported documents and query them during the active session.
- **Hybrid Retrieval** — combines dense vector retrieval with BM25 sparse retrieval.
- **RRF Fusion** — merges dense and sparse rankings using Reciprocal Rank Fusion.
- **Cross-Encoder Reranking** — locally reranks retrieved candidates to improve final context quality.
- **Conditional Query Rewriting** — rewrites weak or context-dependent queries only when retrieval requires it.
- **Session Isolation** — temporary documents are scoped to the user/session and cannot be retrieved across sessions.
- **Single-Ingestion Workflow** — uploaded files are hashed and indexed once instead of being reprocessed for every query.
- **Source Citations** — responses expose document, page/section and chunk metadata for retrieved evidence.
- **Provider Abstraction** — LLM providers are accessed through a common interface.
- **Provider Resilience** — supports provider fallback and circuit-breaker behavior.
- **Zero-Cost Guardrails** — application-level token budgets, rolling limits, concurrency controls and provider enable/disable controls.
- **Caching** — retrieval, LLM and session-aware caches reduce repeated computation and inference.
- **Prompt-Injection Defense** — retrieved documents are treated as untrusted data rather than instructions.
- **Upload Security** — file type, size, page, text-length and parser-resource limits.
- **Session Lifecycle Management** — server-side TTL with cleanup of temporary session data.
- **Operational Metrics** — request, retrieval, provider, quota and latency information.
- **Evaluation Suite** — retrieval, generation, citation and latency evaluation utilities.
- **Dockerized Deployment** — FastAPI, PostgreSQL, Redis and Qdrant can be run through Docker Compose.

---

## 🏗️ Architecture

```text
                    Client / Portfolio Website
                              │
                              ▼
                         FastAPI API
                              │
              ┌───────────────┴────────────────┐
              │                                │
       Rate Limits /                     Session State
       Security / Quotas                 Redis + PostgreSQL
              │                                │
              └───────────────┬────────────────┘
                              ▼
                         Query Pipeline
                              │
              ┌───────────────┴────────────────┐
              │                                │
        Portfolio KB                    Session KB
        Persistent                     Temporary
              │                                │
              └───────────────┬────────────────┘
                              ▼
                    Dense + BM25 Retrieval
                              │
                              ▼
                       RRF Rank Fusion
                              │
                              ▼
                   Cross-Encoder Reranker
                              │
                              ▼
                    Metadata / Session
                       Access Filtering
                              │
                              ▼
                    Context + Citations
                              │
                              ▼
                      Provider Router
                              │
                    ┌─────────┴─────────┐
                    │                   │
                  Groq                Ollama
                Provider            Local Fallback
                    │                   │
                    └─────────┬─────────┘
                              ▼
                       Cat Persona Layer
                              │
                              ▼
                    Grounded Response
                    + Source Metadata
```

---

## 🔍 Retrieval Pipeline

The retrieval pipeline is designed to improve both semantic and exact-term matching.

```text
User Query
    │
    ▼
Query Normalization
    │
    ▼
Dense Vector Retrieval ─────┐
                            │
BM25 Sparse Retrieval ──────┤
                            ▼
                       RRF Fusion
                            │
                            ▼
                    Cross-Encoder
                       Reranking
                            │
                            ▼
                  Session / Metadata
                     Access Filter
                            │
                            ▼
                   Context Assembly
                            │
                            ▼
                    LLM Generation
```

Dense retrieval handles semantic similarity while BM25 provides stronger exact keyword matching. RRF combines both ranked lists before the local cross-encoder performs final reranking.

---

## 📄 Document Ingestion

Uploaded documents follow a bounded ingestion pipeline:

```text
Upload
  ↓
File Validation
  ↓
Size / Page / Text Limits
  ↓
SHA-256 Hash
  ↓
Duplicate Check
  ↓
Document Parsing
  ↓
Text Cleaning
  ↓
Chunking
  ↓
Local Embeddings
  ↓
Qdrant
  ↓
PostgreSQL Metadata
```

A document is indexed once and the resulting representation is reused for subsequent questions during the session.

Temporary document vectors and metadata are removed when their session lifecycle expires.

---

## 🔐 Security

The backend treats both user prompts and uploaded documents as untrusted input.

Implemented controls include:

- Request rate limiting
- Session-specific rate limiting
- Upload rate limiting
- Request-body limits
- File-type validation
- Upload size limits
- PDF page limits
- Extracted-text limits
- Parser concurrency limits
- Parser execution timeouts
- Session/user metadata filtering
- Prompt-injection defenses
- LLM concurrency limits
- Application-level token budgets
- Provider circuit breakers
- Server-side provider credentials
- Protected operational metrics
- Session-aware cache keys

Retrieved document text is explicitly treated as **data**, not as instructions capable of overriding the system policy.

---

## 💰 Zero-Mandatory-Spend Design

The application is designed so that external inference is protected by application-side limits rather than relying only on provider-side free quotas.

The runtime includes:

- Daily application token budget
- Rolling token budget
- Per-session token budget
- Provider token budget
- Per-request token limits
- Token-estimation safety margin
- LLM concurrency limits
- Provider enable/disable controls
- Optional provider fallback
- Provider circuit breakers

The application can stop inference when its configured budget is exhausted instead of automatically allowing additional usage.

Provider quotas, model availability and pricing can change, so provider-specific limits are intentionally configurable rather than hardcoded as permanent guarantees.

---

## 🧠 Memory & Data Lifecycle

The system separates persistent portfolio knowledge from temporary visitor state.

### Persistent

- Portfolio knowledge
- Explicitly saved user preferences

### Session-scoped

- Conversation history
- Uploaded documents
- Document metadata
- Retrieval state
- Temporary session state

Sessions use a server-side TTL. Activity refreshes the TTL, while expiration triggers cleanup of temporary session state and document vectors.

---

## ⚡ Caching

The application contains multiple cache layers:

- File/incremental ingestion caching
- Embedding caching
- BM25 index caching
- Retrieval caching
- LLM response caching
- Session state caching

Cache keys include relevant versions and session/document scope where required to prevent cross-session data leakage and stale results.

---

## 🔌 LLM Provider Abstraction

The RAG engine communicates with providers through an abstraction layer instead of coupling retrieval logic to a specific vendor.

Current provider implementations include:

- Groq
- Ollama

The architecture allows provider availability, quotas and failures to be handled outside the core retrieval pipeline.

---

## 📊 Evaluation

The project includes a versioned evaluation dataset and evaluation utilities for:

### Retrieval

- Hit rate
- Context precision/recall
- Mean Reciprocal Rank
- Retrieval latency

### Generation

- Answer relevance
- Faithfulness
- Manually verified correctness

### Citations

- Citation presence
- Citation validity
- Source evidence mapping
- Document/page metadata

### Operations

- Request latency
- Retrieval latency
- Reranker scores
- Provider/model information
- Token usage
- Rate-limit outcomes
- Provider errors
- Fallback behavior

Evaluation scripts are available under:

```text
app/evaluation/
evaluation/
scripts/
```

---

## 🧪 Testing

The repository contains tests covering major components including:

```text
tests/
├── retrieval
├── reranking
├── embeddings
├── ingestion
├── upload security
├── session management
├── caching
├── rate limiting
├── LLM quotas
├── provider routing
├── provider failures
├── prompt injection
├── Qdrant
├── API routes
├── citations/context
├── cleanup
└── evaluation
```

Run the test suite with:

```bash
pytest -q
```

---

## 🐳 Running Locally

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd meowski-clean
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Configure the required database, Redis, Qdrant and LLM provider settings.

### 3. Start the infrastructure

```bash
docker compose up --build
```

This starts:

```text
FastAPI
PostgreSQL
Redis
Qdrant
```

### 4. Ingest portfolio knowledge

```bash
python scripts/ingest_portfolio.py
```

### 5. Run the API

The API is exposed under:

```text
/api/v1
```

---

## 🔗 API Surface

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/session` | Create a session |
| `GET` | `/api/v1/session` | Get session state |
| `POST` | `/api/v1/chat` | Chat with grounded responses |
| `POST` | `/api/v1/documents` | Upload a temporary document |
| `GET` | `/api/v1/documents` | List session documents |
| `DELETE` | `/api/v1/documents/{id}` | Delete a temporary document |
| `POST` | `/api/v1/preferences` | Save an explicit preference |
| `DELETE` | `/api/v1/preferences/{id}` | Delete a saved preference |
| `GET` | `/api/v1/health` | API/dependency health |
| `GET` | `/api/v1/metrics` | Protected operational metrics |

---

## 📁 Project Structure

```text
meowski-clean/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── evaluation/
│   ├── graph/
│   ├── ingestion/
│   ├── llm/
│   ├── middleware/
│   ├── rag/
│   ├── retrieval/
│   ├── schemas/
│   ├── services/
│   └── vectorstore/
│
├── data/
│   └── portfolio.txt
│
├── evaluation/
│   └── dataset.json
│
├── scripts/
│
├── tests/
│
├── docs/
│   ├── architecture.md
│   ├── cloudflare.md
│   ├── deployment.md
│   ├── evaluation.md
│   └── threat-model.md
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-runtime.txt
├── requirements-dev.txt
├── .env.example
└── README.md
```

---

## 🎯 Design Principles

The project follows several architectural constraints:

1. **Portfolio knowledge is persistent; visitor uploads are temporary.**
2. **Temporary documents are isolated by session/user metadata.**
3. **Documents are ingested once and reused.**
4. **Retrieval and memory are separate concepts.**
5. **The LLM provider is replaceable.**
6. **External inference is protected by application-level budgets.**
7. **Retrieved documents are untrusted data.**
8. **Citations expose the evidence used for grounded answers.**
9. **Security and cost controls are part of the architecture rather than post-processing.**
10. **The backend remains independently usable through an HTTP API.**

---

## 📚 Documentation

Additional design documentation:

- `docs/architecture.md` — system architecture and data boundaries
- `docs/threat-model.md` — security threats and mitigations
- `docs/deployment.md` — local and public deployment considerations
- `docs/evaluation.md` — evaluation methodology
- `docs/cloudflare.md` — edge protection/deployment boundary

---

## 🚀 Project Goal

Cat RAG is designed as a portfolio project demonstrating practical RAG engineering beyond basic vector search, including:

**hybrid retrieval → ranking → session isolation → cost controls → provider resilience → security → evaluation → deployment**

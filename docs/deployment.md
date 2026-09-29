# Deployment

## Local / self-hosted

`docker compose up --build` starts the API, PostgreSQL, Redis and Qdrant. Persistent volumes keep database/vector/cache data across container restarts.

## Public deployment

Recommended boundary:

```text
Visitor → Cloudflare/WAF → FastAPI → PostgreSQL / Redis / Qdrant
```

Configure the edge for coarse abuse controls and rate limiting. Keep provider keys only in server-side environment/secret configuration. Do not expose Qdrant, Redis or PostgreSQL directly to the browser.

Provider quotas, free tiers, model availability and pricing are volatile. Verify the provider's current official documentation before deployment and keep application budgets below the provider's published limits.

# Cloudflare edge controls

The repository intentionally does not hard-code an account-specific Cloudflare configuration. For public deployment, put the API behind Cloudflare and configure:

- WAF/basic managed rules where available.
- Coarse request-rate controls before traffic reaches FastAPI.
- Request/body limits appropriate to the API.
- TLS termination at the edge.
- A trusted origin path to the FastAPI service.

The application remains responsible for per-session/per-IP limits, token budgets, upload limits and concurrency controls.

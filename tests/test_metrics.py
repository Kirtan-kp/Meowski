from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes.metrics import router

def test_metrics_endpoint():
    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)

    response = client.get("/metrics")

    assert response.status_code == 200

    body = response.json()

    assert "metrics" in body
    assert "recent_requests" in body


def test_metrics_token_is_required_when_configured(monkeypatch):
    from app.core.config import settings
    from app.api.routes.metrics import get_observability_service

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_observability_service] = lambda: type("Obs", (), {"get_metrics": lambda self: {"metrics": {}, "recent_requests": []}})()
    monkeypatch.setattr(settings, "metrics_token", "secret")

    response = TestClient(app).get("/metrics")
    assert response.status_code == 401

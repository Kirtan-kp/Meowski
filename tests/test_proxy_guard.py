
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.middleware.proxy_guard import proxy_guard_middleware


def _app():
    app = FastAPI()
    app.middleware("http")(proxy_guard_middleware)

    @app.get("/api/v1/health")
    def health():
        return {"ok": True}


    from fastapi import Request

    @app.get("/api/v1/who")
    def who(request: Request):
        return {"ip": request.state.client_ip}

    return app


def test_open_when_no_secret(monkeypatch):
    monkeypatch.setattr(settings, "proxy_secret", "")
    assert TestClient(_app()).get("/api/v1/who").status_code == 200


def test_blocks_without_or_with_wrong_secret(monkeypatch):
    monkeypatch.setattr(settings, "proxy_secret", "s3cret")
    c = TestClient(_app())
    assert c.get("/api/v1/who").status_code == 403
    assert c.get("/api/v1/who", headers={"X-Proxy-Secret": "nope"}).status_code == 403


def test_health_stays_open(monkeypatch):
    monkeypatch.setattr(settings, "proxy_secret", "s3cret")
    assert TestClient(_app()).get("/api/v1/health").status_code == 200


def test_valid_secret_uses_visitor_ip(monkeypatch):
    monkeypatch.setattr(settings, "proxy_secret", "s3cret")
    r = TestClient(_app()).get("/api/v1/who", headers={"X-Proxy-Secret": "s3cret", "X-Visitor-IP": "203.0.113.9"})
    assert r.status_code == 200 and r.json()["ip"] == "203.0.113.9"

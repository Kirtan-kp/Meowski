from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware import rate_limit

def test_health_bypasses_rate_limit():
    app = FastAPI()
    app.middleware("http")(rate_limit.rate_limit_middleware)

    @app.get("/health")
    def health():
        return {"status" : "ok"}

    client = TestClient(app)

    for _ in range(20):
        response = client.get("/health")
        assert response.status_code == 200

def test_chat_returns_429_when_rate_limit_exceeded(monkeypatch):
    app = FastAPI()
    app.middleware("http")(rate_limit.rate_limit_middleware)

    @app.post("/chat")
    def chat():
        return {"message" : "ok"}

    monkeypatch.setattr(rate_limit.rate_limit_service , "is_allowed" , lambda **kwargs : False)
    client = TestClient(app)
    response = client.post("/chat")
    assert response.status_code == 429
    assert response.json() == {"detail" : "Rate limit exceeded"}

def test_versioned_chat_path_is_rate_limited(monkeypatch):
    app = FastAPI()
    app.middleware("http")(rate_limit.rate_limit_middleware)

    @app.post("/api/v1/chat")
    def chat():
        return {"message": "ok"}

    monkeypatch.setattr(rate_limit.rate_limit_service, "is_allowed", lambda **kwargs: False)
    response = TestClient(app).post("/api/v1/chat")

    assert response.status_code == 429


def test_versioned_document_path_is_rate_limited(monkeypatch):
    app = FastAPI()
    app.middleware("http")(rate_limit.rate_limit_middleware)

    @app.post("/api/v1/documents")
    def documents():
        return {"message": "ok"}

    monkeypatch.setattr(rate_limit.rate_limit_service, "is_allowed", lambda **kwargs: False)
    response = TestClient(app).post("/api/v1/documents")

    assert response.status_code == 429


def test_large_request_body_is_rejected(monkeypatch):
    app = FastAPI()
    app.middleware("http")(rate_limit.rate_limit_middleware)

    @app.post("/api/v1/chat")
    def chat():
        return {"message": "ok"}

    monkeypatch.setattr(rate_limit.settings, "max_request_body_bytes", 10)
    response = TestClient(app).post("/api/v1/chat", content="01234567890")
    assert response.status_code == 413

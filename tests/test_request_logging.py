from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.request_logging import request_logging_middleware


def create_app():

    app = FastAPI()

    app.middleware("http")(request_logging_middleware)

    @app.get("/test")
    async def test_endpoint(request: Request):

        return {
            "request_id": request.state.request_id
        }

    return app


def test_request_id_is_generated():

    client = TestClient(create_app())

    response = client.get("/test")

    assert response.status_code == 200

    request_id = response.json()["request_id"]

    assert request_id
    assert len(request_id) == 36


def test_request_id_is_returned_in_response_header():

    client = TestClient(create_app())

    response = client.get("/test")

    assert response.status_code == 200

    request_id = response.json()["request_id"]

    assert response.headers["X-Request-ID"] == request_id


def test_each_request_gets_unique_request_id():

    client = TestClient(create_app())

    response_1 = client.get("/test")
    response_2 = client.get("/test")

    request_id_1 = response_1.json()["request_id"]
    request_id_2 = response_2.json()["request_id"]

    assert request_id_1 != request_id_2
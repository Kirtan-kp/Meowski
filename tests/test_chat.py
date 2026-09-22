from fastapi.testclient import TestClient
from app.main import app
from app.api.routes.chat import get_chat_service
from app.schemas.retrieval import RetrievalResponse, Source

class FakeChatService:

    def generate_response(self, message, session_id, user_id , request_id):

        return RetrievalResponse(
            answer="Kirtan built a RAG chatbot using Qdrant.",
            sources=[
                Source(
                    content="The project uses Qdrant for vector retrieval.",
                    metadata={
                        "file_id": "file_1",
                        "scope": "portfolio"
                    }
                )
            ]
        )


def test_chat_response_includes_sources():

    app.dependency_overrides[get_chat_service] = lambda: FakeChatService()

    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "What project uses Qdrant?",
            "session_id": "session_1",
            "user_id": "user_1"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["response"] == "Kirtan built a RAG chatbot using Qdrant."

    assert len(data["sources"]) == 1

    assert data["sources"][0]["content"] == (
        "The project uses Qdrant for vector retrieval."
    )

    assert data["sources"][0]["metadata"]["file_id"] == "file_1"
    assert data["sources"][0]["metadata"]["scope"] == "portfolio"

    app.dependency_overrides.clear()

def test_chat_response_handles_empty_sources():

    class FakeChatService:

        def generate_response(self, message, session_id, user_id , request_id):

            return RetrievalResponse(
                answer=(
                    "The information is not available "
                    "in the provided context."
                ),
                sources=[]
            )

    app.dependency_overrides[get_chat_service] = lambda: FakeChatService()

    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "What information do you have?",
            "session_id": "session_1",
            "user_id": "user_1"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["response"] == (
        "The information is not available "
        "in the provided context."
    )

    assert data["sources"] == []

    app.dependency_overrides.clear()
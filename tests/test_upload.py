from fastapi.testclient import TestClient
from app.services.upload_service import UploadService
from app.main import app
from app.api.routes.upload import get_upload_service
import pytest
from app.ingestion.validators import validate_file

class FakeDB:

    def add(self , record):
        self.record = record

    def commit(self):
        pass

db = FakeDB()

class FakeUploadService:

    def __init__(self):
        self.uploaded_chunks = []

    def upload(self, file, user_id, session_id):
        self.uploaded_chunks.append(
            {
                "filename": file.filename,
                "user_id": user_id,
                "session_id": session_id
            }
        )

        return [object()]

fake_upload_service = FakeUploadService()

def override_upload_service():
    return fake_upload_service

@pytest.fixture
def upload_service_override():

    app.dependency_overrides[get_upload_service] = override_upload_service
    yield
    app.dependency_overrides.pop(get_upload_service , None)

client = TestClient(app)

def test_upload_txt_file(upload_service_override):
    response = client.post(
        "/upload",
        files={
            "file": (
                "cat_test.txt",
                "Milo is an orange cat. His favorite food is tuna.",
                "text/plain"
            )
        },
        data={
            "user_id": "test_user",
            "session_id": "test_session"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "File uploaded successfully"
    assert data["chunks"] == 1

    assert fake_upload_service.uploaded_chunks[-1] == {
        "filename": "cat_test.txt",
        "user_id": "test_user",
        "session_id": "test_session"
    }

def test_upload_rejects_unsupported_file_type():
    with pytest.raises(ValueError):
        validate_file("cat.exe", 100)


def test_upload_rejects_oversized_file():
    with pytest.raises(ValueError):
        validate_file("cat.txt", 10 * 1024 * 1024 + 1)

def test_upload_adds_chunks_to_vector_store(tmp_path):

    class FakeVectorStore:

        def __init__(self):
            self.documents = None

        def add_documents(self, documents):
            self.documents = documents
            return []

    class FakeUploadFile:

        def __init__(self, file):
            self.filename = "cat_test.txt"
            self.file = file

    vector_store = FakeVectorStore()

    file_path = tmp_path / "cat_test.txt"

    file_path.write_text(
        "Milo is an orange cat. His favorite food is tuna.",
        encoding="utf-8"
    )

    with open(file_path, "rb") as file:

        upload_file = FakeUploadFile(file)

        service = UploadService(vector_store , db)

        chunks = service.upload(
            file=upload_file,
            user_id="test_user",
            session_id="test_session"
        )
    assert db.record.id
    assert db.record.user_id == "test_user"
    assert db.record.session_id == "test_session"
    assert db.record.scope == "session"
    assert db.record.status == "ready"
    assert len(chunks) > 0
    assert vector_store.documents is not None
    assert len(vector_store.documents) > 0

    for chunk in vector_store.documents:
        assert chunk.metadata["user_id"] == "test_user"
        assert chunk.metadata["session_id"] == "test_session"
        assert chunk.metadata["scope"] == "session"
        assert chunk.metadata["file_id"]
        assert chunk.metadata["created_at"]
        assert chunk.metadata["expires_at"]
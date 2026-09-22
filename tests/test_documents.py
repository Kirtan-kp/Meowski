from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.databse import Base
from app.db.models import FileRecord, SessionRecord
from app.main import app
from app.api.routes.upload import get_upload_service
from app.services.upload_service import UploadService


class FakeSessionService:

    def get_session(self, session_id, user_id):
        return True


class FakeVectorStore:

    def __init__(self):
        self.deleted_file_ids = []

    def delete_by_file_id(self, file_id):
        self.deleted_file_ids.append(file_id)


class FakeBM25IndexService:

    def __init__(self):
        self.invalidated_sessions = []

    def invalidate_session(self, user_id, session_id):
        self.invalidated_sessions.append(
            (user_id, session_id)
        )


class FakeRetrievalCacheService:

    def __init__(self):
        self.invalidations = 0

    def invalidate(self):
        self.invalidations += 1


def create_database():

    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    return engine, SessionLocal()


def create_session_record(
    db,
    *,
    session_id="session_1",
    user_id="user_1",
):

    now = datetime.now(timezone.utc)

    session = SessionRecord(
        id=session_id,
        user_id=user_id,
        status="active",
        created_at=now,
        expires_at=now + timedelta(hours=24),
    )

    db.add(session)
    db.commit()

    return session


def create_file_record(
    db,
    *,
    document_id="doc_1",
    user_id="user_1",
    session_id="session_1",
    filename="cat.txt",
    status="ready",
):

    now = datetime.now(timezone.utc)

    document = FileRecord(
        id=document_id,
        user_id=user_id,
        session_id=session_id,
        filename=filename,
        file_hash=f"hash-{document_id}",
        scope="session",
        status=status,
        created_at=now,
        expires_at=now + timedelta(hours=24),
    )

    db.add(document)
    db.commit()

    return document


def test_list_documents_returns_only_current_user_session():

    engine, db = create_database()

    create_session_record(
        db,
        session_id="session_1",
        user_id="user_1",
    )

    create_session_record(
        db,
        session_id="session_2",
        user_id="user_1",
    )

    create_session_record(
        db,
        session_id="session_3",
        user_id="user_2",
    )

    create_file_record(
        db,
        document_id="doc_1",
        user_id="user_1",
        session_id="session_1",
    )

    create_file_record(
        db,
        document_id="doc_2",
        user_id="user_1",
        session_id="session_2",
    )

    create_file_record(
        db,
        document_id="doc_3",
        user_id="user_2",
        session_id="session_3",
    )

    service = UploadService(
        vector_store=FakeVectorStore(),
        db=db,
        session_service=FakeSessionService(),
    )

    documents = service.list_documents(
        user_id="user_1",
        session_id="session_1",
    )

    assert len(documents) == 1
    assert documents[0].id == "doc_1"

    db.close()
    engine.dispose()


def test_list_documents_excludes_deleted_documents():

    engine, db = create_database()

    create_session_record(db)

    create_file_record(
        db,
        document_id="doc_ready",
        status="ready",
    )

    create_file_record(
        db,
        document_id="doc_deleted",
        status="deleted",
    )

    service = UploadService(
        vector_store=FakeVectorStore(),
        db=db,
        session_service=FakeSessionService(),
    )

    documents = service.list_documents(
        user_id="user_1",
        session_id="session_1",
    )

    assert len(documents) == 1
    assert documents[0].id == "doc_ready"

    db.close()
    engine.dispose()


def test_delete_document_removes_vector_and_invalidates_caches():

    engine, db = create_database()

    create_session_record(db)

    create_file_record(
        db,
        document_id="doc_1",
    )

    vector_store = FakeVectorStore()
    bm25_service = FakeBM25IndexService()
    retrieval_cache_service = FakeRetrievalCacheService()

    service = UploadService(
        vector_store=vector_store,
        db=db,
        session_service=FakeSessionService(),
        bm25_index_service=bm25_service,
        retrieval_cache_service=retrieval_cache_service,
    )

    deleted = service.delete_document(
        document_id="doc_1",
        user_id="user_1",
        session_id="session_1",
    )

    assert deleted is True

    assert vector_store.deleted_file_ids == [
        "doc_1"
    ]

    assert bm25_service.invalidated_sessions == [
        ("user_1", "session_1")
    ]

    assert retrieval_cache_service.invalidations == 1

    document = db.get(
        FileRecord,
        "doc_1",
    )

    assert document.status == "deleted"

    db.close()
    engine.dispose()


def test_delete_document_rejects_other_user():

    engine, db = create_database()

    create_session_record(
        db,
        session_id="session_1",
        user_id="user_1",
    )

    create_file_record(
        db,
        document_id="doc_1",
        user_id="user_1",
        session_id="session_1",
    )

    service = UploadService(
        vector_store=FakeVectorStore(),
        db=db,
        session_service=FakeSessionService(),
    )

    deleted = service.delete_document(
        document_id="doc_1",
        user_id="user_2",
        session_id="session_1",
    )

    assert deleted is False

    document = db.get(
        FileRecord,
        "doc_1",
    )

    assert document.status == "ready"

    db.close()
    engine.dispose()


def test_delete_document_rejects_other_session():

    engine, db = create_database()

    create_session_record(
        db,
        session_id="session_1",
        user_id="user_1",
    )

    create_session_record(
        db,
        session_id="session_2",
        user_id="user_1",
    )

    create_file_record(
        db,
        document_id="doc_1",
        user_id="user_1",
        session_id="session_1",
    )

    service = UploadService(
        vector_store=FakeVectorStore(),
        db=db,
        session_service=FakeSessionService(),
    )

    deleted = service.delete_document(
        document_id="doc_1",
        user_id="user_1",
        session_id="session_2",
    )

    assert deleted is False

    document = db.get(
        FileRecord,
        "doc_1",
    )

    assert document.status == "ready"

    db.close()
    engine.dispose()


class FakeDocumentAPIService:

    def __init__(self):
        self.documents = [
            type(
                "Document",
                (),
                {
                    "id": "doc_1",
                    "filename": "cat.txt",
                    "status": "ready",
                    "scope": "session",
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": (
                        datetime.now(timezone.utc)
                        + timedelta(hours=24)
                    ),
                },
            )()
        ]

        self.deleted_ids = []

    def list_documents(self, *, user_id, session_id):
        return self.documents

    def delete_document(
        self,
        *,
        document_id,
        user_id,
        session_id,
    ):
        if document_id not in {
            document.id for document in self.documents
        }:
            return False

        self.deleted_ids.append(document_id)
        return True


def test_list_documents_api():

    fake_service = FakeDocumentAPIService()

    app.dependency_overrides[
        get_upload_service
    ] = lambda: fake_service

    client = TestClient(app)

    response = client.get(
        "/api/v1/documents",
        params={
            "user_id": "user_1",
            "session_id": "session_1",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["document_id"] == "doc_1"
    assert data[0]["filename"] == "cat.txt"

    app.dependency_overrides.clear()


def test_delete_document_api():

    fake_service = FakeDocumentAPIService()

    app.dependency_overrides[
        get_upload_service
    ] = lambda: fake_service

    client = TestClient(app)

    response = client.delete(
        "/api/v1/documents/doc_1",
        params={
            "user_id": "user_1",
            "session_id": "session_1",
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "Document deleted successfully"
    )

    assert fake_service.deleted_ids == ["doc_1"]

    app.dependency_overrides.clear()


def test_delete_document_api_returns_404():

    fake_service = FakeDocumentAPIService()

    app.dependency_overrides[
        get_upload_service
    ] = lambda: fake_service

    client = TestClient(app)

    response = client.delete(
        "/api/v1/documents/does-not-exist",
        params={
            "user_id": "user_1",
            "session_id": "session_1",
        },
    )

    assert response.status_code == 404

    app.dependency_overrides.clear()
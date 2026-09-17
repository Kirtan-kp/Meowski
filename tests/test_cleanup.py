from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from langchain_core.documents import Document
from app.db.models import FileRecord
from app.db.databse import SessionLocal
from app.services.cleanup_service import CleanupService
from uuid import uuid4

file_id = str(uuid4())

class FakeDB:
    def __init__(self, files, sessions):
        self.files = files
        self.sessions = sessions
        self.committed = False

    def execute(self, statement):
        class Result:
            def __init__(self, items):
                self.items = items

            def scalars(self):
                return self

            def all(self):
                return self.items

        entity = statement.column_descriptions[0]["entity"]

        if entity.__name__ == "FileRecord":
            return Result(self.files)

        return Result(self.sessions)

    def commit(self):
        self.committed = True


class FakeVectorStore:
    def __init__(self):
        self.deleted_file_ids = []

    def delete_by_file_id(self, file_id):
        self.deleted_file_ids.append(file_id)


class FakeStateService:
    def __init__(self):
        self.deleted_session_ids = []

    def delete_state(self, session_id):
        self.deleted_session_ids.append(session_id)


def test_cleanup_expired_files():
    expired_file = SimpleNamespace(
        id="file-1",
        scope="session",
        status="ready",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    db = FakeDB(
        files=[expired_file],
        sessions=[],
    )

    vector_store = FakeVectorStore()

    service = CleanupService(
        db=db,
        vector_store=vector_store,
    )

    result = service.cleanup_expired_files()

    assert result == ["file-1"]
    assert vector_store.deleted_file_ids == ["file-1"]
    assert expired_file.status == "expired"
    assert db.committed is True


def test_cleanup_expired_sessions():
    expired_session = SimpleNamespace(
        id="session-1",
        status="active",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    db = FakeDB(
        files=[],
        sessions=[expired_session],
    )

    vector_store = FakeVectorStore()
    state_service = FakeStateService()

    session_service = SimpleNamespace(
        state_service=state_service
    )

    service = CleanupService(
        db=db,
        vector_store=vector_store,
        session_service=session_service,
    )

    result = service.cleanup_expired_sessions()

    assert result == ["session-1"]
    assert expired_session.status == "expired"
    assert state_service.deleted_session_ids == ["session-1"]
    assert db.committed is True

def test_cleanup_expired_file_removes_qdrant_vectors():
    from app.vectorstore.qdrant_store import QdrantVectorStore
    from uuid import uuid4

    vector_store = QdrantVectorStore(embedding_dimension=384)

    vector_store.client.delete_collection(
        collection_name=vector_store.collection_name
    )

    vector_store._create_collection_if_not_exists(
        embedding_dimension=384
    )

    file_id = str(uuid4())

    document = Document(
        page_content="This document should be deleted after expiry.",
        metadata={
            "file_id": file_id,
            "scope": "session",
            "user_id": "user_1",
            "session_id": "session_1",
        },
    )

    vector_store.add_documents([document])

    results_before = vector_store.similarity_search(
        "document should be deleted",
        k=10,
    )

    assert any(
        doc.metadata.get("file_id") == file_id
        for doc in results_before
    )

    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        file_record = FileRecord(
            id=file_id,
            user_id="user_1",
            session_id="session_1",
            filename="cleanup.txt",
            file_hash="cleanup-hash",
            scope="session",
            status="ready",
            created_at=now - timedelta(hours=25),
            expires_at=now - timedelta(hours=1),
        )

        db.add(file_record)
        db.commit()

        service = CleanupService(
            db=db,
            vector_store=vector_store,
        )

        result = service.cleanup_expired_files()

        assert file_id in result

        db.refresh(file_record)
        assert file_record.status == "expired"

        results_after = vector_store.similarity_search(
            "document should be deleted",
            k=10,
        )

        assert not any(
            doc.metadata.get("file_id") == file_id
            for doc in results_after
        )

    finally:
        db.rollback()
        db.close()
import io
from unittest.mock import patch
from app.services.upload_service import UploadService

class FakeSessionService:

    def get_session(self, session_id, user_id):
        return True

class FakeResult:

    def __init__(self, record=None):
        self.record = record

    def scalar_one_or_none(self):
        return self.record


class FakeDB:

    def __init__(self):
        self.records = []

    def add(self, record):
        self.records.append(record)

    def commit(self):
        pass

    def execute(self, statement):

        for record in self.records:

            if (
                record.user_id == statement._where_criteria[0].right.value
                and record.session_id == statement._where_criteria[1].right.value
                and record.file_hash == statement._where_criteria[2].right.value
                and record.status == statement._where_criteria[3].right.value
            ):
                return FakeResult(record)

        return FakeResult()


class FakeVectorStore:

    def __init__(self):
        self.add_calls = 0
        self.documents = []

    def add_documents(self, documents):
        self.add_calls += 1
        self.documents = documents
        return []

    def get_documents(self, file_id):
        return self.documents


class FakeUploadFile:

    def __init__(self, content, filename="test.txt"):
        self.filename = filename
        self.file = io.BytesIO(content)


def test_first_upload_ingests_file():

    db = FakeDB()
    vector_store = FakeVectorStore()

    service = UploadService(vector_store, db , FakeSessionService())

    with patch(
        "app.services.upload_service.IngestionService.ingest"
    ) as mock_ingest:

        mock_ingest.return_value = []

        service.upload(
            file=FakeUploadFile(b"Meowski is a cat."),
            user_id="user_1",
            session_id="session_1"
        )

        assert mock_ingest.call_count == 1
        assert vector_store.add_calls == 1


def test_same_file_same_session_uses_cache():

    db = FakeDB()
    vector_store = FakeVectorStore()

    service = UploadService(vector_store, db , FakeSessionService())

    with patch(
        "app.services.upload_service.IngestionService.ingest"
    ) as mock_ingest:

        mock_ingest.return_value = []

        service.upload(
            file=FakeUploadFile(b"Meowski is a cat."),
            user_id="user_1",
            session_id="session_1"
        )

        service.upload(
            file=FakeUploadFile(b"Meowski is a cat."),
            user_id="user_1",
            session_id="session_1"
        )

        assert mock_ingest.call_count == 1
        assert vector_store.add_calls == 1


def test_same_file_different_session_is_ingested():

    db = FakeDB()
    vector_store = FakeVectorStore()

    service = UploadService(vector_store, db , FakeSessionService())

    with patch(
        "app.services.upload_service.IngestionService.ingest"
    ) as mock_ingest:

        mock_ingest.return_value = []

        service.upload(
            file=FakeUploadFile(b"Meowski is a cat."),
            user_id="user_1",
            session_id="session_1"
        )

        service.upload(
            file=FakeUploadFile(b"Meowski is a cat."),
            user_id="user_1",
            session_id="session_2"
        )

        assert mock_ingest.call_count == 2
        assert vector_store.add_calls == 2


def test_different_file_same_session_is_ingested():

    db = FakeDB()
    vector_store = FakeVectorStore()

    service = UploadService(vector_store, db , FakeSessionService())

    with patch(
        "app.services.upload_service.IngestionService.ingest"
    ) as mock_ingest:

        mock_ingest.return_value = []

        service.upload(
            file=FakeUploadFile(b"Meowski is a cat."),
            user_id="user_1",
            session_id="session_1"
        )

        service.upload(
            file=FakeUploadFile(b"Meowski is a dog."),
            user_id="user_1",
            session_id="session_1"
        )

        assert mock_ingest.call_count == 2
        assert vector_store.add_calls == 2
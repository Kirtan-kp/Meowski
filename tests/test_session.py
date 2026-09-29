import pytest
from app.services.session_service import SessionService
from datetime import datetime , timezone , timedelta
from app.core.config import settings

class FakeDB:
    def __init__(self):
        self.records = []

    def add(self, record):
        self.records.append(record)

    def commit(self):
        pass

    def query(self, model):
        return FakeQuery(self.records)


class FakeQuery:
    def __init__(self, records):
        self.records = records
        self.conditions = []

    def filter(self, *conditions):
        self.conditions = conditions
        return self

    def first(self):
        for record in self.records:
            matches = True
            for condition in self.conditions:
                if condition.left.key == "id":
                    matches &= record.id == condition.right.value
                elif condition.left.key == "user_id":
                    matches &= record.user_id == condition.right.value
            if matches:
                return record
        return None

    def update(self, values, synchronize_session=False):
        updated = 0
        for record in self.records:
            matches = True
            for condition in self.conditions:
                key = getattr(condition.left, "key", None)
                expected = getattr(getattr(condition, "right", None), "value", None)
                if expected is None:
                    continue
                if hasattr(record, key):
                    matches &= getattr(record, key) == expected
            if matches:
                for column, value in values.items():
                    setattr(record, column.key, value)
                updated += 1
        return updated


class FakeStateService:
    def __init__(self):
        self.states = {}
        self.ttls = {}

    def save_state(self, session_id, state, ttl_seconds):
        self.states[session_id] = state
        self.ttls[session_id] = ttl_seconds

    def get_state(self, session_id):
        return self.states.get(session_id)

    def delete_state(self, session_id):
        self.states.pop(session_id, None)
        self.ttls.pop(session_id, None)

    def refresh_ttl(self, session_id, ttl_seconds):
        if session_id in self.states:
            self.ttls[session_id] = ttl_seconds


def test_create_session():
    db = FakeDB()
    state_service = FakeStateService()

    service = SessionService(
        db=db,
        state_service=state_service
    )

    session = service.create_session("user_1")

    assert session.id
    assert session.user_id == "user_1"
    assert session.status == "active"
    assert session.created_at <= session.expires_at

    assert state_service.get_state(session.id) == {}


def test_get_session_requires_correct_user():
    db = FakeDB()
    state_service = FakeStateService()

    service = SessionService(
        db=db,
        state_service=state_service
    )

    session = service.create_session("user_1")

    result = service.get_session(
        session_id=session.id,
        user_id="user_1"
    )

    assert result.id == session.id

    with pytest.raises(ValueError, match="Session not found"):
        service.get_session(
            session_id=session.id,
            user_id="user_2"
        )


def test_session_state():
    db = FakeDB()
    state_service = FakeStateService()

    service = SessionService(
        db=db,
        state_service=state_service
    )

    session = service.create_session("user_1")

    state = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }

    service.save_state(
        session_id=session.id,
        user_id="user_1",
        state=state
    )

    result = service.get_state(
        session_id=session.id,
        user_id="user_1"
    )

    assert result == state


def test_delete_session():
    db = FakeDB()
    state_service = FakeStateService()

    service = SessionService(
        db=db,
        state_service=state_service
    )

    session = service.create_session("user_1")

    service.delete_session(
        session_id=session.id,
        user_id="user_1"
    )

    assert session.status == "deleted"
    assert state_service.get_state(session.id) is None

def test_session_state_persists_across_service_instances():
    db = FakeDB()
    state_service = FakeStateService()

    service_one = SessionService(
        db=db,
        state_service=state_service
    )

    session = service_one.create_session("user_1")

    state = {
        "chat_history": [
            {
                "role": "user",
                "content": "My name is Kirtan"
            },
            {
                "role": "assistant",
                "content": "Nice to meet you!"
            }
        ]
    }

    service_one.save_state(
        session_id=session.id,
        user_id="user_1",
        state=state
    )

    # Simulate a new request creating a new service instance.
    service_two = SessionService(
        db=db,
        state_service=state_service
    )

    recovered_state = service_two.get_state(
        session_id=session.id,
        user_id="user_1"
    )

    assert recovered_state == state

def test_session_state_uses_configured_ttl():
    db = FakeDB()
    state_service = FakeStateService()

    service = SessionService(
        db=db,
        state_service=state_service
    )

    session = service.create_session("user_1")

    assert state_service.ttls[session.id] == settings.session_ttl_seconds

def test_expired_session_is_rejected_and_state_deleted():
    db = FakeDB()
    state_service = FakeStateService()

    service = SessionService(
        db=db,
        state_service=state_service
    )

    session = service.create_session("user_1")

    state_service.save_state(
        session_id=session.id,
        state={"chat_history": []},
        ttl_seconds=100
    )

    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    with pytest.raises(ValueError, match="Session has expired"):
        service.get_session(
            session_id=session.id,
            user_id="user_1"
        )

    assert session.status == "expired"
    assert state_service.get_state(session.id) is None

def test_saving_state_refreshes_session_ttl():
    db = FakeDB()
    state_service = FakeStateService()

    service = SessionService(
        db=db,
        state_service=state_service
    )

    session = service.create_session("user_1")

    session.expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=300)
    )

    service.save_state(
        session_id=session.id,
        user_id="user_1",
        state={"chat_history": []}
    )

    assert (
        settings.session_ttl_seconds - 5
        <= state_service.ttls[session.id]
        <= settings.session_ttl_seconds
    )
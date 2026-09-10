from datetime import datetime, timezone

import pytest

from app.services.session_service import SessionService


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


class FakeStateService:
    def __init__(self):
        self.states = {}

    def save_state(self, session_id, state, ttl_seconds):
        self.states[session_id] = state

    def get_state(self, session_id):
        return self.states.get(session_id)

    def delete_state(self, session_id):
        self.states.pop(session_id, None)


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
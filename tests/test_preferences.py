from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.databse import Base
from app.main import app
from app.api.routes.preferences import get_preference_service
from app.services.preference_service import PreferenceService


class FakePreference:

    def __init__(
        self,
        preference_id,
        user_id,
        key,
        value,
    ):
        self.id = preference_id
        self.user_id = user_id
        self.key = key
        self.value = value
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at


class FakePreferenceService:

    def __init__(self):
        self.preferences = {}

    def save_preference(self, *, user_id, key, value):

        preference_key = (user_id, key)

        if preference_key in self.preferences:
            preference = self.preferences[preference_key]
            preference.value = value
            preference.updated_at = datetime.now(timezone.utc)
            return preference

        preference = FakePreference(
            preference_id=f"pref-{len(self.preferences) + 1}",
            user_id=user_id,
            key=key,
            value=value,
        )

        self.preferences[preference_key] = preference

        return preference

    def get_preferences(self, *, user_id):
        return [
            preference
            for (stored_user_id, _), preference
            in self.preferences.items()
            if stored_user_id == user_id
        ]

    def delete_preference(self, *, preference_id, user_id):

        for key, preference in list(self.preferences.items()):

            if (
                preference.id == preference_id
                and preference.user_id == user_id
            ):
                del self.preferences[key]
                return True

        return False


def test_preference_service_save_and_get():

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()

    service = PreferenceService(db)

    preference = service.save_preference(
        user_id="user_1",
        key="response_style",
        value="concise",
    )

    assert preference.id
    assert preference.user_id == "user_1"
    assert preference.key == "response_style"
    assert preference.value == "concise"

    preferences = service.get_preferences(
        user_id="user_1",
    )

    assert len(preferences) == 1
    assert preferences[0].value == "concise"

    db.close()


def test_preference_service_updates_existing_key():

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()

    service = PreferenceService(db)

    first = service.save_preference(
        user_id="user_1",
        key="response_style",
        value="concise",
    )

    second = service.save_preference(
        user_id="user_1",
        key="response_style",
        value="detailed",
    )

    assert first.id == second.id
    assert second.value == "detailed"

    preferences = service.get_preferences(
        user_id="user_1",
    )

    assert len(preferences) == 1
    assert preferences[0].value == "detailed"

    db.close()


def test_preference_service_isolates_users():

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()

    service = PreferenceService(db)

    service.save_preference(
        user_id="user_1",
        key="response_style",
        value="concise",
    )

    service.save_preference(
        user_id="user_2",
        key="response_style",
        value="detailed",
    )

    user_1_preferences = service.get_preferences(
        user_id="user_1",
    )

    user_2_preferences = service.get_preferences(
        user_id="user_2",
    )

    assert len(user_1_preferences) == 1
    assert user_1_preferences[0].value == "concise"

    assert len(user_2_preferences) == 1
    assert user_2_preferences[0].value == "detailed"

    db.close()


def test_preference_service_delete_requires_correct_user():

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()

    service = PreferenceService(db)

    preference = service.save_preference(
        user_id="user_1",
        key="response_style",
        value="concise",
    )

    deleted = service.delete_preference(
        preference_id=preference.id,
        user_id="user_2",
    )

    assert deleted is False

    preferences = service.get_preferences(
        user_id="user_1",
    )

    assert len(preferences) == 1

    deleted = service.delete_preference(
        preference_id=preference.id,
        user_id="user_1",
    )

    assert deleted is True

    assert service.get_preferences(
        user_id="user_1",
    ) == []

    db.close()


def test_create_preference_api():

    fake_service = FakePreferenceService()

    app.dependency_overrides[
        get_preference_service
    ] = lambda: fake_service

    client = TestClient(app)

    response = client.post(
        "/api/v1/preferences",
        json={
            "user_id": "user_1",
            "key": "response_style",
            "value": "concise",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == "user_1"
    assert data["key"] == "response_style"
    assert data["value"] == "concise"

    app.dependency_overrides.clear()


def test_delete_preference_api():

    fake_service = FakePreferenceService()

    preference = fake_service.save_preference(
        user_id="user_1",
        key="response_style",
        value="concise",
    )

    app.dependency_overrides[
        get_preference_service
    ] = lambda: fake_service

    client = TestClient(app)

    response = client.delete(
        f"/api/v1/preferences/{preference.id}",
        params={
            "user_id": "user_1",
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "Preference deleted successfully"
    )

    app.dependency_overrides.clear()


def test_delete_preference_api_rejects_other_user():

    fake_service = FakePreferenceService()

    preference = fake_service.save_preference(
        user_id="user_1",
        key="response_style",
        value="concise",
    )

    app.dependency_overrides[
        get_preference_service
    ] = lambda: fake_service

    client = TestClient(app)

    response = client.delete(
        f"/api/v1/preferences/{preference.id}",
        params={
            "user_id": "user_2",
        },
    )

    assert response.status_code == 404

    app.dependency_overrides.clear()
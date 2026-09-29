from datetime import datetime, timedelta, timezone
import uuid
from app.db.models import SessionRecord, FileRecord
from app.services.session_state_service import SessionStateService
from app.core.config import settings

class SessionError(ValueError):
    """Base class for session problems (subclasses ValueError for backward compatibility)."""

class SessionNotFoundError(SessionError):
    pass

class SessionInactiveError(SessionError):
    pass

class SessionExpiredError(SessionError):
    pass

class SessionService:

    def __init__(self , db , state_service : SessionStateService):
        self.db = db
        self.state_service = state_service

    def create_session(self , user_id : str):
        session_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(seconds=settings.session_ttl_seconds)

        session = SessionRecord(id = session_id , user_id = user_id , status = "active",
            created_at = created_at , expires_at = expires_at)

        self.db.add(session)
        self.db.commit()
        self.state_service.save_state(session_id = session_id , state = {} , ttl_seconds = settings.session_ttl_seconds)

        return session

    def get_session(self , session_id : str , user_id : str):
        session = (self.db.query(SessionRecord).filter(SessionRecord.id == session_id , SessionRecord.user_id == user_id).first())

        if session is None:
            raise SessionNotFoundError("Session not found")

        now = datetime.now(timezone.utc)

        if session.status != "active":
            raise SessionInactiveError("Session is not active")

        if session.expires_at <= now:
            session.status = "expired"
            self.db.commit()

            self.state_service.delete_state(session_id)

            raise SessionExpiredError("Session has expired")

        session.expires_at = now + timedelta(seconds=settings.session_ttl_seconds)
        self.db.query(FileRecord).filter(
            FileRecord.user_id == user_id,
            FileRecord.session_id == session_id,
            FileRecord.scope == "session",
            FileRecord.status.in_(["processing", "ready"]),
        ).update(
            {FileRecord.expires_at: session.expires_at},
            synchronize_session=False,
        )
        self.db.commit()
        self.state_service.refresh_ttl(session_id, settings.session_ttl_seconds)
        return session

    def save_state(self , session_id : str , user_id : str , state : dict):

        session = self.get_session(session_id = session_id , user_id = user_id)
        remaining_seconds = max(1 , int((session.expires_at - datetime.now(timezone.utc)).total_seconds()))
        self.state_service.save_state(session_id = session_id , state = state , ttl_seconds = min(remaining_seconds, settings.session_ttl_seconds))

    def get_state(self , session_id : str , user_id : str):

        self.get_session(session_id = session_id , user_id = user_id)

        return self.state_service.get_state(session_id)

    def delete_session(self , session_id : str , user_id : str):

        session = self.get_session(session_id = session_id , user_id = user_id)
        session.status = "deleted"
        self.db.commit()
        self.state_service.delete_state(session_id)
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.models import FileRecord, SessionRecord


class CleanupService:
    def __init__(self, db, vector_store, session_service=None):
        self.db = db
        self.vector_store = vector_store
        self.session_service = session_service

    def cleanup_expired_files(self):
        now = datetime.now(timezone.utc)

        expired_files = self.db.execute(
            select(FileRecord).where(
                FileRecord.scope == "session",
                FileRecord.status == "ready",
                FileRecord.expires_at <= now,
            )
        ).scalars().all()

        deleted_file_ids = []

        for file_record in expired_files:
            self.vector_store.delete_by_file_id(file_record.id)

            file_record.status = "expired"
            deleted_file_ids.append(file_record.id)

        if expired_files:
            self.db.commit()

        return deleted_file_ids

    def cleanup_expired_sessions(self):
        now = datetime.now(timezone.utc)

        expired_sessions = self.db.execute(
            select(SessionRecord).where(
                SessionRecord.status == "active",
                SessionRecord.expires_at <= now,
            )
        ).scalars().all()

        expired_session_ids = []

        for session in expired_sessions:
            session.status = "expired"
            expired_session_ids.append(session.id)

            if self.session_service:
                self.session_service.state_service.delete_state(session.id)

        if expired_sessions:
            self.db.commit()

        return expired_session_ids

    def cleanup(self):
        expired_files = self.cleanup_expired_files()
        expired_sessions = self.cleanup_expired_sessions()

        return {
            "expired_files": expired_files,
            "expired_sessions": expired_sessions,
        }
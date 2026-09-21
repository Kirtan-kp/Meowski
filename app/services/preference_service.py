from datetime import datetime, timezone
import uuid

from sqlalchemy import select

from app.db.models import PreferenceRecord


class PreferenceService:

    def __init__(self, db):
        self.db = db

    def save_preference(
        self,
        *,
        user_id: str,
        key: str,
        value: str,
    ) -> PreferenceRecord:

        now = datetime.now(timezone.utc)

        preference = self.db.execute(
            select(PreferenceRecord).where(
                PreferenceRecord.user_id == user_id,
                PreferenceRecord.key == key,
            )
        ).scalar_one_or_none()

        if preference is None:

            preference = PreferenceRecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                key=key,
                value=value,
                created_at=now,
                updated_at=now,
            )

            self.db.add(preference)

        else:

            preference.value = value
            preference.updated_at = now

        self.db.commit()
        self.db.refresh(preference)

        return preference

    def get_preferences(
        self,
        *,
        user_id: str,
    ) -> list[PreferenceRecord]:

        return list(
            self.db.execute(
                select(PreferenceRecord)
                .where(
                    PreferenceRecord.user_id == user_id,
                )
                .order_by(PreferenceRecord.key)
            ).scalars().all()
        )

    def delete_preference(
        self,
        *,
        preference_id: str,
        user_id: str,
    ) -> bool:

        preference = self.db.execute(
            select(PreferenceRecord).where(
                PreferenceRecord.id == preference_id,
                PreferenceRecord.user_id == user_id,
            )
        ).scalar_one_or_none()

        if preference is None:
            return False

        self.db.delete(preference)
        self.db.commit()

        return True
from datetime import datetime
from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.databse import Base

class FileRecord(Base):

    __tablename__ = "files"

    id : Mapped[str] = mapped_column(String , primary_key = True)
    user_id : Mapped[str] = mapped_column(String , nullable = False , index = True)
    session_id : Mapped[str] = mapped_column(String , nullable = False , index = True)
    filename : Mapped[str] = mapped_column(String , nullable = False)
    file_hash : Mapped[str] = mapped_column(String , nullable = False , index = True)
    scope : Mapped[str] = mapped_column(String , nullable = False)
    status : Mapped[str] = mapped_column(String , nullable = False)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone = True) , nullable = False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone = True) , nullable = False)

class SessionRecord(Base):
     
    __tablename__ = "sessions"

    id : Mapped[str] = mapped_column(String , primary_key = True)
    user_id : Mapped[str] = mapped_column(String , nullable = False , index = True)
    status : Mapped[str] = mapped_column(String , nullable = False)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone = True) , nullable = False)
    expires_at : Mapped[datetime] = mapped_column(DateTime(timezone = True) , nullable = False)

class PreferenceRecord(Base):

    __tablename__ = "preferences"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "key",
            name="uq_preference_user_key",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

    user_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    key: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
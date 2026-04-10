# FILE: backend/src/models.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT
#   PURPOSE: SQLAlchemy ORM модели: StoredFile и Alert. Cascade delete алертов при удалении файла.
#   SCOPE: ORM model definitions, table schema, relationships
#   DEPENDS: M-DB (Base class)
#   LINKS: M-MODELS, V-M-MODELS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   Base - DeclarativeBase for Alembic and all models
#   StoredFile - File entity with scan/processing state and relationship to alerts
#   Alert - Alert entity with FK to files, cascade deleted with parent file
# END_MODULE_MAP

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# START_BLOCK_STORED_FILE_MODEL
class StoredFile(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded")
    scan_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scan_details: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    requires_attention: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
# END_BLOCK_STORED_FILE_MODEL


# START_BLOCK_ALERT_MODEL
class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False
    )
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    file: Mapped["StoredFile"] = relationship("StoredFile", back_populates="alerts")
# END_BLOCK_ALERT_MODEL

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.1.0 - Added cascade relationship: StoredFile.alerts with delete-orphan,
#                  Alert.file back_populates, FK ondelete=CASCADE. Added GRACE markup.]
# END_CHANGE_SUMMARY

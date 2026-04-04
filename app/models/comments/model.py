"""
Модель комментария (Comment) для сервиса совместных поездок RoadMate.

Комментарии - это простые сообщения между пользователями, не привязанные к поездкам.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CommentStatus(str, PyEnum):
    """Статусы комментария."""
    DRAFT = "draft"
    PUBLISHED = "published"
    DELETED = "deleted"


class Comment(Base):
    """Модель комментария."""

    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор комментария",
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="ID автора комментария",
    )

    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="ID пользователя, которому адресован комментарий",
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Текст комментария",
    )

    status: Mapped[CommentStatus] = mapped_column(
        Enum(
            CommentStatus,
            name="comment_status",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=CommentStatus.PUBLISHED,
        index=True,
        comment="Статус комментария",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Время создания",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Время последнего обновления",
    )

    author: Mapped["User"] = relationship(
        "User",
        back_populates="comments_written",
        foreign_keys=[author_id],
    )

    target: Mapped["User"] = relationship(
        "User",
        back_populates="comments_received",
        foreign_keys=[target_id],
    )

    __table_args__ = (
        Index("ix_comments_author_id", "author_id"),
        Index("ix_comments_target_id", "target_id"),
        Index("ix_comments_status", "status"),
        Index("ix_comments_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, author_id={self.author_id}, target_id={self.target_id})>"


from app.models.users.model import User
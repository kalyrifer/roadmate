
"""
Модель отзыва (Review) для сервиса совместных поездок RoadMate.

Отзывы создаются участниками поездки после её завершения.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReviewStatus(str, PyEnum):
    """Статусы отзыва."""
    PENDING = "pending"       # Ожидает модерации
    PUBLISHED = "published"   # Опубликован
    REJECTED = "rejected"     # Отклонен


class Review(Base):
    """Модель отзыва."""

    __tablename__ = "reviews"

    # === Основные идентификаторы ===
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор отзыва",
    )

    # === Связь с поездкой ===
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "trips.id",
            ondelete="CASCADE",  # При удалении поездки удаляются отзывы
        ),
        nullable=False,
        index=True,
        comment="ID поездки",
    )

    # === Связь с автором отзыва ===
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",  # При удалении пользователя удаляются его отзывы
        ),
        nullable=False,
        index=True,
        comment="ID автора отзыва",
    )

    # === Связь с пользователем, о котором отзыв ===
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",  # При удалении пользователя удаляются отзывы о нём
        ),
        nullable=False,
        index=True,
        comment="ID пользователя, о котором оставлен отзыв",
    )

    # === Содержимое отзыва ===
    rating: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="Оценка от 1 до 5",
    )
    text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Текст отзыва",
    )

    # === Статус ===
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(
            ReviewStatus,
            name="review_status",
            native_enum=False,  # Используем VARCHAR вместо PostgreSQL enum
            values_callable=lambda x: [e.value for e in x],  # Приводим к lowercase
        ),
        nullable=False,
        default=ReviewStatus.PUBLISHED,
        index=True,
        comment="Статус отзыва",
    )

    # === Служебные поля ===
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

    # === Связи (Relationships) ===

    # Поездка
    trip: Mapped["Trip"] = relationship(
        "Trip",
        back_populates="reviews",
    )

    # Автор отзыва
    author: Mapped["User"] = relationship(
        "User",
        back_populates="reviews_given",
        foreign_keys=[author_id],
    )

    # Пользователь, о котором отзыв
    target: Mapped["User"] = relationship(
        "User",
        back_populates="reviews_received",
        foreign_keys=[target_id],
    )

    # === Индексы и ограничения ===
    __table_args__ = (
        # Уникальный индекс: один отзыв от одного автора о одном участнике на одну поездку
        UniqueConstraint("trip_id", "author_id", "target_id", name="uq_reviews_trip_author_target"),
        # Индексы для быстрого поиска
        Index("ix_reviews_trip_id", "trip_id"),
        Index("ix_reviews_author_id", "author_id"),
        Index("ix_reviews_target_id", "target_id"),
        Index("ix_reviews_status", "status"),
        Index("ix_reviews_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, trip_id={self.trip_id}, author_id={self.author_id}, rating={self.rating})>"


# Импорты для избежания циклических зависимостей
from app.models.trips.model import Trip  # noqa: E402
from app.models.users.model import User  # noqa: E402
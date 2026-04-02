"""
Модель уведомления (Notification) для сервиса совместных поездок RoadMate.

Уведомления создаются при важных событиях в системе: новые заявки, подтверждения,
отклонения, сообщения и т.д.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NotificationType(str, PyEnum):
    """Типы уведомлений."""
    # Заявки на бронирование
    REQUEST_NEW = "request_new"           # Новый запрос на бронирование
    REQUEST_CONFIRMED = "request_confirmed"  # Запрос подтверждён
    REQUEST_REJECTED = "request_rejected"    # Запрос отклонён
    REQUEST_CANCELLED = "request_cancelled"  # Запрос отменён
    
    # Поездки
    TRIP_CANCELLED = "trip_cancelled"     # Поездка отменена
    TRIP_COMPLETED = "trip_completed"     # Поездка завершена
    
    # Чат
    MESSAGE_NEW = "message_new"           # Новое сообщение в чате
    
    # Системные
    SYSTEM = "system"                      # Системное уведомление


class Notification(Base):
    """Модель уведомления."""

    __tablename__ = "notifications"

    # === Основные идентификаторы ===
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор уведомления",
    )

    # === Связь с пользователем ===
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",  # При удалении пользователя удаляются уведомления
        ),
        nullable=False,
        index=True,
        comment="ID получателя уведомления",
    )

    # === Содержание уведомления ===
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False,
        index=True,
        comment="Тип уведомления",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Заголовок уведомления",
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Текст уведомления",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Прочитано ли уведомление",
    )

    # === Связи с другими сущностями (nullable для сохранения истории) ===
    related_trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "trips.id",
            ondelete="SET NULL",  # При удалении поездки уведомление сохраняется
        ),
        nullable=True,
        index=True,
        comment="ID связанной поездки",
    )
    related_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "trip_requests.id",
            ondelete="SET NULL",  # При удалении заявки уведомление сохраняется
        ),
        nullable=True,
        index=True,
        comment="ID связанной заявки",
    )
    related_conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
        comment="ID связанного чата",
    )

    # === Служебные поля ===
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время прочтения",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Время создания",
    )

    # === Связи (Relationships) ===

    # Пользователь-получатель
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
    )

    # Связанная поездка (опционально)
    related_trip: Mapped["Trip | None"] = relationship(
        "Trip",
        foreign_keys=[related_trip_id],
    )

    # Связанная заявка (опционально)
    related_request: Mapped["TripRequest | None"] = relationship(
        "TripRequest",
        foreign_keys=[related_request_id],
    )

    # === Индексы ===
    __table_args__ = (
        # Индекс для выборки уведомлений пользователя
        Index("ix_notifications_user_id", "user_id"),
        # Индекс для фильтрации по статусу прочтения
        Index("ix_notifications_is_read", "is_read"),
        # Индекс для сортировки по дате
        Index("ix_notifications_created_at", "created_at"),
        # Составной индекс для основного запроса (пользователь + непрочитанные)
        Index(
            "ix_notifications_user_unread",
            "user_id",
            "is_read",
        ),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, is_read={self.is_read})>"


# Импорты для избежания циклических зависимостей
from app.models.users.model import User  # noqa: E402
from app.models.trips.model import Trip  # noqa: E402
from app.models.requests.model import TripRequest  # noqa: E402

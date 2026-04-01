"""
Модель настроек пользователя (UserSettings) для сервиса совместных поездок RoadMate.

Связь ONE-TO-ONE с User. Хранит индивидуальные настройки пользователя.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserSettings(Base):
    """Модель настроек пользователя."""

    __tablename__ = "user_settings"

    # === Основные идентификаторы ===
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор настроек",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",  # Удаляются вместе с пользователем
        ),
        nullable=False,
        unique=True,
        index=True,
        comment="ID пользователя",
    )

    # === Настройки интерфейса ===
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ru",
        comment="Язык интерфейса (ru, en)",
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Europe/Moscow",
        comment="Часовой пояс",
    )
    theme: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="light",
        comment="Тема оформления (light, dark)",
    )

    # === Настройки уведомлений ===
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Включены ли уведомления",
    )
    email_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Уведомления на email",
    )
    push_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Push-уведомления",
    )
    telegram_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Уведомления в Telegram",
    )
    trip_request_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Уведомления о заявках",
    )
    message_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Уведомления о сообщениях",
    )
    review_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Уведомления об отзывах",
    )
    marketing_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Маркетинговые уведомления",
    )

    # === Настройки приватности ===
    privacy_show_profile: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Показывать профиль",
    )
    privacy_show_phone: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Показывать телефон",
    )
    privacy_show_last_seen: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Показывать последний визит",
    )

    # === Служебные поля ===
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Настройки активны",
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
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время мягкого удаления",
    )

    # === Связи (Relationships) ===
    user: Mapped["User"] = relationship(
        "User",
        back_populates="settings",
    )

    # === Индексы ===
    __table_args__ = (
        Index("ix_user_settings_user_id", "user_id", unique=True),
        Index("ix_user_settings_language", "language"),
        Index("ix_user_settings_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id}, language={self.language})>"


from app.models.users.model import User  # noqa: E402
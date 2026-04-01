"""
Модель пользователя (User) для сервиса совместных поездок RoadMate.

Пользователь — центральная сущность системы. Один аккаунт может выступать как
водитель (создаёт поездки) и как пассажир (бронирует поездки).
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, PyEnum):
    """Роли пользователей в системе."""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """Модель пользователя системы."""

    __tablename__ = "users"

    # === Основные идентификаторы ===
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор пользователя",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Email пользователя (уникальный, используется для входа)",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Хэш пароля (bcrypt)",
    )

    # === Профильная информация ===
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Имя пользователя",
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Фамилия пользователя",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Номер телефона",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL аватара",
    )
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Описание профиля",
    )

    # === Рейтинговая система ===
    rating_average: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=0.00,
        comment="Средний рейтинг (0.00-5.00)",
    )
    rating_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Количество отзывов",
    )

    # === Статусы и права ===
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
        index=True,
        comment="Роль пользователя",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Активность аккаунта",
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Блокировка администратором",
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Подтверждение email",
    )
    is_phone_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Подтверждение телефона",
    )
    is_two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Включена двухфакторная аутентификация",
    )

    # === Настройки и локализация ===
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

    # === Служебные поля ===
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время последнего входа",
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
        index=True,
        comment="Время мягкого удаления",
    )

    # === Связи (Relationships) ===

    # Поездки, созданные пользователем (как водитель)
    trips_as_driver: Mapped[list["Trip"]] = relationship(
        "Trip",
        back_populates="driver",
        foreign_keys="Trip.driver_id",
    )

    # Заявки на бронирование (как пассажир)
    trip_requests: Mapped[list["TripRequest"]] = relationship(
        "TripRequest",
        back_populates="passenger",
        foreign_keys="TripRequest.passenger_id",
    )

    # Диалоги (участник чата)
    chat_participations: Mapped[list["ConversationParticipant"]] = relationship(
        "ConversationParticipant",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Отправленные сообщения
    sent_messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.sender_id",
        cascade="all, delete-orphan",
    )

    # Отзывы (автор и получатель)
    reviews_given: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="author",
        foreign_keys="Review.author_id",
    )
    reviews_received: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="target",
        foreign_keys="Review.target_id",
    )

    # Уведомления
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Аудит действий
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Настройки пользователя (one-to-one)
    settings: Mapped["UserSettings"] = relationship(
        "UserSettings",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # === Индексы ===
    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_phone", "phone"),
        Index("ix_users_role", "role"),
        Index("ix_users_is_active", "is_active"),
        Index("ix_users_is_blocked", "is_blocked"),
        Index("ix_users_deleted_at", "deleted_at"),
        Index("ix_users_rating_average", "rating_average"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.first_name} {self.last_name})>"


# Импорты для избежания циклических зависимостей
from app.models.trips import Trip  # noqa: E402
from app.models.requests import TripRequest  # noqa: E402
from app.models.chat import ConversationParticipant, Message  # noqa: E402
from app.models.reviews import Review  # noqa: E402
from app.models.notifications import Notification  # noqa: E402
from app.models.admin import AuditLog  # noqa: E402
from app.models.users import UserSettings  # noqa: E402
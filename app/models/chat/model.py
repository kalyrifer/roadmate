"""
Модели чатов для сервиса совместных поездок RoadMate.

Сущности:
- Conversation — диалог между участниками поездки
- ConversationParticipant — участник чата с настройками
- Message — сообщение в чате
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.users.model import User
    from app.models.trips.model import Trip


class Conversation(Base):
    """Модель диалога (чата) между участниками поездки."""

    __tablename__ = "conversations"

    # === Основные идентификаторы ===
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор чата",
    )

    # === Связь с поездкой ===
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "trips.id",
            ondelete="CASCADE",  # При удалении поездки удаляются чаты
        ),
        nullable=False,
        index=True,
        comment="ID поездки",
    )

    # === Служебные поля ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Время создания чата",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Время последнего обновления",
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Время последнего сообщения",
    )

    # === Связи (Relationships) ===

    # Поездка
    trip: Mapped["Trip"] = relationship(
        "Trip",
        back_populates="conversations",
    )

    # Участники чата
    participants: Mapped[list["ConversationParticipant"]] = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Сообщения
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # === Индексы ===
    __table_args__ = (
        Index("ix_conversations_trip_id", "trip_id"),
        Index("ix_conversations_last_message_at", "last_message_at"),
        Index("ix_conversations_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, trip_id={self.trip_id})>"


class ConversationParticipant(Base):
    """Модель участника чата."""

    __tablename__ = "conversation_participants"

    # === Основные идентификаторы ===
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор участника",
    )

    # === Связь с чатом ===
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="ID чата",
    )

    # === Связь с пользователем ===
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="ID пользователя",
    )

    # === Настройки участника ===
    is_muted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Отключены ли уведомления",
    )

    # === Ссылка на последнее прочитанное сообщение ===
    last_read_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "messages.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        comment="ID последнего прочитанного сообщения",
    )

    # === Временные метки ===
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Время входа в чат",
    )

    # === Связи (Relationships) ===

    # Чат
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="participants",
    )

    # Пользователь
    user: Mapped["User"] = relationship(
        "User",
        back_populates="chat_participations",
    )

    # Последнее прочитанное сообщение
    last_read_message: Mapped["Message | None"] = relationship(
        "Message",
        foreign_keys=[last_read_message_id],
    )

    # === Индексы ===
    __table_args__ = (
        Index("ix_conversation_participants_conversation_id", "conversation_id"),
        Index("ix_conversation_participants_user_id", "user_id"),
        Index("ix_conversation_participants_joined_at", "joined_at"),
        # Уникальный индекс: один пользователь может быть только один раз в чате
        Index(
            "ix_conversation_participants_unique",
            "conversation_id",
            "user_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<ConversationParticipant(id={self.id}, user_id={self.user_id}, conversation_id={self.conversation_id})>"


class Message(Base):
    """Модель сообщения в чате."""

    __tablename__ = "messages"

    # === Основные идентификаторы ===
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор сообщения",
    )

    # === Связь с чатом ===
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="ID чата",
    )

    # === Связь с отправителем ===
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=False,
        index=True,
        comment="ID отправителя",
    )

    # === Содержимое сообщения ===
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Текст сообщения",
    )

    # === Статус прочтения ===
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Прочитано ли сообщение",
    )

    # === Служебные поля ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Время отправки",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Время последнего обновления",
    )

    # === Связи (Relationships) ===

    # Чат
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )

    # Отправитель
    sender: Mapped["User"] = relationship(
        "User",
        back_populates="sent_messages",
    )

    # === Индексы ===
    __table_args__ = (
        Index("ix_messages_conversation_id", "conversation_id"),
        Index("ix_messages_sender_id", "sender_id"),
        Index("ix_messages_created_at", "created_at"),
        Index("ix_messages_is_read", "is_read"),
        # Составной индекс для сортировки сообщений в чате
        Index(
            "ix_messages_conversation_created",
            "conversation_id",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, sender_id={self.sender_id}, conversation_id={self.conversation_id})>"


# Импорты для избежания циклических зависимостей
from app.models.trips.model import Trip  # noqa: E402
from app.models.users.model import User  # noqa: E402
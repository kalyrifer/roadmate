"""
Pydantic схемы для чатов (Chat).

Сущности:
- ConversationCreate/Read — создание и чтение чатов
- ConversationParticipantRead — чтение участников чата
- MessageCreate/Read — создание и чтение сообщений
- ConversationList — список чатов с пагинацией
- MessageList — список сообщений с пагинацией
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.chat.model import Conversation, ConversationParticipant, Message


# === Базовые схемы ===

class ConversationBase(BaseModel):
    """Базовая схема чата."""
    pass


class MessageBase(BaseModel):
    """Базовая схема сообщения."""
    pass


class ConversationParticipantBase(BaseModel):
    """Базовая схема участника чата."""
    pass


# === Схемы создания ===

class ConversationCreate(ConversationBase):
    """Схема для создания чата."""
    trip_id: UUID = Field(..., description="ID поездки")
    participant_ids: list[UUID] = Field(..., min_length=2, max_length=10, description="ID участников (минимум 2)")


class ConversationByTripCreate(BaseModel):
    """Схема для создания чата по поездке с первым сообщением."""
    trip_id: UUID = Field(..., description="ID поездки")
    content: str = Field(default="", description="Текст первого сообщения (опционально)")


class MessageCreate(MessageBase):
    """Схема для создания сообщения."""
    content: str = Field(..., min_length=1, max_length=5000, description="Текст сообщения")


# === Схемы обновления ===

class ConversationParticipantUpdate(ConversationParticipantBase):
    """Схема для обновления участника чата."""
    is_muted: Optional[bool] = Field(None, description="Отключить/включить уведомления")


class ConversationMuteUpdate(BaseModel):
    """Схема для управления уведомлениями."""
    is_muted: bool = Field(..., description="True - отключить уведомления, False - включить")


class MessageReadUpdate(BaseModel):
    """Схема для отметки сообщений как прочитанных."""
    message_id: UUID = Field(..., description="ID сообщения")


# === Схемы чтения (ответы API) ===

class UserBrief(BaseModel):
    """Краткая информация о пользователе."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None


class ConversationParticipantRead(ConversationParticipantBase):
    """Схема для чтения участника чата."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    user_id: UUID
    is_muted: bool
    last_read_message_id: Optional[UUID] = None
    joined_at: datetime
    user: Optional[UserBrief] = None


class TripBrief(BaseModel):
    """Краткая информация о поездке."""
    id: str = ""
    from_city: str = ""
    to_city: str = ""
    departure_date: Optional[str] = None
    departure_time_start: Optional[str] = None


class ConversationRead(ConversationBase):
    """Схема для чтения чата."""
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',  # Ignore extra fields from model
    )

    id: UUID
    trip_id: UUID
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    participants: list[ConversationParticipantRead] = []
    last_message: Optional["MessageRead"] = None
    trip: Optional[dict] = None  # Flexible - can be dict with trip info or None


class MessageRead(MessageBase):
    """Схема для чтения ��ообщения."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_id: UUID
    sender: Optional[UserBrief] = None
    content: str
    is_read: bool
    created_at: datetime
    updated_at: datetime


# === Схемы списков с пагинацией ===

class ConversationList(BaseModel):
    """Схема для списка чатов."""
    items: list[ConversationRead]
    total: int
    page: int
    page_size: int
    pages: int


class MessageList(BaseModel):
    """Схема для списка сообщений."""
    items: list[MessageRead]
    total: int
    page: int
    page_size: int
    pages: int


# === Схемы для создания ответа API ===

class ConversationCreateResponse(ConversationRead):
    """Схема ответа при создании чата."""
    pass


class MessageCreateResponse(MessageRead):
    """Схема ответа при отправке сообщения."""
    pass


# Резолвим forward-references (ConversationRead.last_message → MessageRead).
ConversationRead.model_rebuild()
ConversationCreateResponse.model_rebuild()


# === WebSocket схемы ===

class WebSocketMessage(BaseModel):
    """Схема сообщения для WebSocket."""
    type: str = Field(..., description="Тип сообщения: message, read, typing")
    conversation_id: UUID
    message: Optional[MessageRead] = None
    message_id: Optional[UUID] = None
    user_id: Optional[UUID] = None


class WebSocketConnection(BaseModel):
    """Схема подключения для WebSocket."""
    conversation_id: UUID
    user_id: UUID
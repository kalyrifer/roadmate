"""
Service слой для работы с чатами (Chat).

Экспорты:
- ChatService — основной Service для чатов
- ChatServiceError — базовый класс ошибок
- ChatNotFoundError — чат не найден
- TripNotFoundError — поездка не найдена
- NotParticipantError — не участник поездки
- NotConversationParticipantError — не участник чата
- ForbiddenError — нет прав доступа
"""
from app.services.chat.service import (
    ChatService,
    ChatServiceError,
    ChatNotFoundError,
    ForbiddenError,
    NotConversationParticipantError,
    NotParticipantError,
    TripNotFoundError,
)

__all__ = [
    "ChatService",
    "ChatServiceError",
    "ChatNotFoundError",
    "TripNotFoundError",
    "NotParticipantError",
    "NotConversationParticipantError",
    "ForbiddenError",
]

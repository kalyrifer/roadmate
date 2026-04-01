"""
Модели чатов для сервиса совместных поездок RoadMate.

Экспорты:
- Conversation — диалог между участниками поездки
- ConversationParticipant — участник чата с настройками
- Message — сообщение в чате
"""
from app.models.chat.model import (
    Conversation,
    ConversationParticipant,
    Message,
)

__all__ = [
    "Conversation",
    "ConversationParticipant",
    "Message",
]

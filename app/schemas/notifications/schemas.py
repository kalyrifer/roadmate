"""
Pydantic схемы для уведомлений.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.notifications.model import NotificationType


class NotificationBase(BaseModel):
    """Базовая схема уведомления."""
    type: NotificationType
    title: str = Field(..., max_length=255)
    message: str
    is_read: bool = False


class NotificationCreate(NotificationBase):
    """Схема для создания уведомления."""
    user_id: UUID
    related_trip_id: Optional[UUID] = None
    related_request_id: Optional[UUID] = None


class NotificationUpdate(BaseModel):
    """Схема для обновления уведомления."""
    is_read: bool


class NotificationResponse(NotificationBase):
    """Схема ответа с данными уведомления."""
    id: UUID
    user_id: UUID
    related_trip_id: Optional[UUID] = None
    related_request_id: Optional[UUID] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    """Статистика по уведомлениям."""
    unread_count: int = 0
    total_count: int = 0


class NotificationListParams(BaseModel):
    """Параметры списка уведомлений."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    is_read: Optional[bool] = None
    type: Optional[NotificationType] = None


class NotificationListResponse(BaseModel):
    """Ответ со списком уведомлений."""
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    pages: int
    stats: NotificationStats

"""
Pydantic схемы для отзывов (Review).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.reviews.model import ReviewStatus


# === Базовая схема ===
class ReviewBase(BaseModel):
    """Базовая схема отзыва."""
    rating: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5")
    text: Optional[str] = Field(None, max_length=2000, description="Текст отзыва")


# === Схема создания ===
class ReviewCreate(ReviewBase):
    """Схема для создания отзыва."""
    trip_id: UUID
    target_id: UUID


# === Схема обновления статуса ===
class ReviewStatusUpdate(BaseModel):
    """Схема для обновления статуса отзыва."""
    status: ReviewStatus


# === Схема ответа (чтение) ===
class ReviewRead(ReviewBase):
    """Схема для чтения отзыва."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    trip_id: UUID
    author_id: UUID
    target_id: UUID
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime


# === Схема для списка с пагинацией ===
class ReviewList(BaseModel):
    """Схема для списка отзывов."""
    items: list[ReviewRead]
    total: int
    page: int
    page_size: int
    pages: int


# === Схема для создания ответа API ===
class ReviewCreateResponse(ReviewRead):
    """Схема ответа при создании отзыва."""
    pass


# === Схема фильтрации ===
class ReviewFilter(BaseModel):
    """Схема фильтрации отзывов."""
    status: Optional[ReviewStatus] = None
    trip_id: Optional[UUID] = None
    author_id: Optional[UUID] = None
    target_id: Optional[UUID] = None


# === Схема для отзыва с информацией об авторе и получателе ===
class ReviewReadWithUsers(ReviewRead):
    """Схема для чтения отзыва с информацией о пользователях."""
    author_first_name: Optional[str] = None
    author_last_name: Optional[str] = None
    target_first_name: Optional[str] = None
    target_last_name: Optional[str] = None
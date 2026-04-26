"""
Pydantic схемы для отзывов (Review).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.models.reviews.model import ReviewStatus


class ReviewUserSummary(BaseModel):
    """Краткая информация об авторе или получателе отзыва."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    avatar_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _build_name(cls, data):
        if hasattr(data, "first_name"):
            first = (getattr(data, "first_name", None) or "").strip()
            last = (getattr(data, "last_name", None) or "").strip()
            full = f"{first} {last}".strip()
            if not full and getattr(data, "email", None):
                full = data.email.split("@")[0]
            return {
                "id": data.id,
                "name": full or "Участник",
                "avatar_url": getattr(data, "avatar_url", None),
            }
        return data


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
    author: Optional[ReviewUserSummary] = None
    target: Optional[ReviewUserSummary] = None


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
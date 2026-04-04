"""
Pydantic схемы для комментариев (Comment).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.comments.model import CommentStatus


class CommentBase(BaseModel):
    """Базовая схема комментария."""
    text: str = Field(..., min_length=1, max_length=2000, description="Текст комментария")


class CommentCreate(CommentBase):
    """Схема для создания комментария."""
    target_id: UUID


class CommentStatusUpdate(BaseModel):
    """Схема для обновления статуса комментария."""
    status: CommentStatus


class CommentRead(CommentBase):
    """Схема для чтения комментария."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    author_id: UUID
    target_id: UUID
    status: CommentStatus
    created_at: datetime
    updated_at: datetime


class CommentList(BaseModel):
    """Схема для списка комментариев с пагинацией."""
    items: list[CommentRead]
    total: int
    page: int
    page_size: int
    pages: int


class CommentCreateResponse(CommentRead):
    """Схема ответа при создании комментария."""
    pass


class CommentFilter(BaseModel):
    """Схема фильтрации комментариев."""
    status: Optional[CommentStatus] = None
    author_id: Optional[UUID] = None
    target_id: Optional[UUID] = None


class CommentReadWithUser(CommentRead):
    """Схема для чтения комментария с информацией о пользователях."""
    author_first_name: Optional[str] = None
    author_last_name: Optional[str] = None
    author_avatar_url: Optional[str] = None
    target_first_name: Optional[str] = None
    target_last_name: Optional[str] = None
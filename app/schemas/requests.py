"""
Pydantic схемы для заявок на бронирование (TripRequest).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.requests.model import TripRequestStatus


# === Базовая схема ===
class TripRequestBase(BaseModel):
    """Базовая схема заявки."""
    seats_requested: int = Field(..., ge=1, le=8, description="Количество мест")
    message: Optional[str] = Field(None, max_length=1000, description="Сообщение водителю")


# === Схема создания ===
class TripRequestCreate(TripRequestBase):
    """Схема для создания заявки."""
    pass


# === Схема обновления ===
class TripRequestUpdate(BaseModel):
    """Схема для обновления статуса заявки."""
    status: Optional[TripRequestStatus] = None
    rejected_reason: Optional[str] = Field(None, max_length=500, description="Причина отклонения")


# === Схема подтверждения/отклонения ===
class TripRequestAction(BaseModel):
    """Схема для действий с заявкой."""
    rejected_reason: Optional[str] = Field(None, max_length=500, description="Причина отклонения")


# === Схема ответа (чтение) ===
class TripRequestRead(TripRequestBase):
    """Схема для чтения заявки."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    trip_id: UUID
    passenger_id: UUID
    status: TripRequestStatus
    confirmed_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# === Схема для списка с пагинацией ===
class TripRequestList(BaseModel):
    """Схема для списка заявок."""
    items: list[TripRequestRead]
    total: int
    page: int
    page_size: int
    pages: int


# === Схема для создания ответа API ===
class TripRequestCreateResponse(TripRequestRead):
    """Схема ответа при создании заявки."""
    pass


# === Схема фильтрации ===
class TripRequestFilter(BaseModel):
    """Схема фильтрации заявок."""
    status: Optional[TripRequestStatus] = None
    trip_id: Optional[UUID] = None
    passenger_id: Optional[UUID] = None
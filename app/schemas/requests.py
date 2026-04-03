"""
Pydantic схемы для заявок на бронирование (TripRequest).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from datetime import datetime, time

from pydantic import BaseModel, Field, ConfigDict, field_serializer

from app.models.requests.model import TripRequestStatus


# === Базовая схема ===
class TripRequestBase(BaseModel):
    """Базовая схема заявки."""
    seats_requested: int = Field(..., gt=0, le=8, description="Количество запрашиваемых мест (от 1 до 8)")
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


# === Схема отклонения заявки ===
class TripRequestRejectRequest(BaseModel):
    """Схема для отклонения заявки."""
    rejection_reason: Optional[str] = Field(None, max_length=500, description="Причина отклонения (комментарий для пассажира)")


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


# === Краткая информация о поездке для деталей заявки ===
class TripRequestTripDetail(BaseModel):
    """Краткая информация о поездке для деталей заявки."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    from_city: str
    to_city: str
    departure_date: datetime
    departure_time_start: time
    
    @field_serializer('departure_time_start')
    def serialize_time(self, value: time) -> str:
        return value.strftime('%H:%M') if value else None


# === Краткая информация о пассажире для деталей заявки ===
class TripRequestPassengerDetail(BaseModel):
    """Краткая информация о пассажире для деталей заявки."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    first_name: str
    last_name: str
    rating_average: Optional[float] = None
    rating_count: Optional[int] = None


# === Полная схема заявки с связанными данными ===
class TripRequestFull(TripRequestRead):
    """Полная схема заявки с связанными данными."""
    trip: Optional[TripRequestTripDetail] = None
    passenger: Optional[TripRequestPassengerDetail] = None


# === Краткая информация о поездке для списка заявок пассажира ===
class TripRequestTripInfo(BaseModel):
    """Краткая информация о поездке для списка заявок."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    from_city: str
    to_city: str
    departure_date: datetime
    departure_time_start: datetime
    available_seats: int


# === Краткая информация о пользователе (пассажире/водителе) ===
class TripRequestUserInfo(BaseModel):
    """Краткая информация о пользователе."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    first_name: str
    last_name: str
    rating_average: Optional[float] = None
    avatar_url: Optional[str] = None


# === Элемент списка заявок для пассажира ===
class TripRequestListItemPassenger(BaseModel):
    """Элемент списка заявок для пассажира."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    trip_id: UUID
    trip: TripRequestTripInfo
    status: TripRequestStatus
    seats_requested: int
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None


# === Элемент списка заявок для водителя ===
class TripRequestListItemDriver(BaseModel):
    """Элемент списка заявок для водителя."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    trip_id: UUID
    passenger: TripRequestUserInfo
    status: TripRequestStatus
    seats_requested: int
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# === Пагинация ===
class PaginationMeta(BaseModel):
    """Мета-информация о пагинации."""
    page: int
    page_size: int
    total: int
    pages: int


# === Список заявок пассажира с пагинацией ===
class TripRequestListPassenger(BaseModel):
    """Список заявок пассажира с пагинацией."""
    data: list[TripRequestListItemPassenger]
    meta: PaginationMeta


# === Список заявок водителя по поездке с пагинацией ===
class TripRequestListDriver(BaseModel):
    """Список заявок водителя по поездке с пагинацией."""
    data: list[TripRequestListItemDriver]
    meta: PaginationMeta


# === Схема для списка с пагинацией (универсальная) ===
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


# === API Response схемы ===

class TripRequestResponseData(BaseModel):
    """Обёртка для данных заявки в ответе API."""
    data: TripRequestRead


class TripRequestActionResponse(BaseModel):
    """Обёртка для ответа при подтверждении/отклонении."""
    data: TripRequestRead
    message: str


class TripRequestCreateAPIResponse(BaseModel):
    """Обёртка для ответа при создании заявки."""
    data: TripRequestRead
    message: str = "Request created"


class TripRequestConfirmAPIResponse(BaseModel):
    """Обёртка для ответа при подтверждении заявки."""
    data: TripRequestRead
    message: str = "Request confirmed"


class TripRequestRejectAPIResponse(BaseModel):
    """Обёртка для ответа при отклонении заявки."""
    data: TripRequestRead
    message: str = "Request rejected"


class TripRequestCancelAPIResponse(BaseModel):
    """Обёртка для ответа при отмене заявки."""
    data: TripRequestRead
    message: str = "Request cancelled"
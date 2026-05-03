"""
Схемы Pydantic для работы с поездками.

Содержит схемы для создания, обновления и отображения поездок.
"""
from datetime import date, date as date_type, time
from typing import Any, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    field_validator,
    model_validator,
)

# Допустимые поля для сортировки
ALLOWED_SORT_BY = ["price", "departure_time", "created_at", "driver_rating"]
ALLOWED_SORT_ORDER = ["asc", "desc"]
MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


class TripSearchFilters(BaseModel):
    """
    Схема для фильтрации и поиска поездок.
    
    Поддерживает базовый поиск по городам, расширенные фильтры,
    сортировку и пагинацию.
    """
    # Базовый поиск по городам (case-insensitive, partial)
    from_city: str | None = Field(None, description="Город отправления (частичный поиск)")
    to_city: str | None = Field(None, description="Город назначения (частичный поиск)")
    
    # Фильтры по дате
    date: Optional[date_type] = Field(None, description="Дата поездки (точное совпадение)")
    date_from: Optional[date_type] = Field(None, description="Дата поездки (начало диапазона)")
    date_to: Optional[date_type] = Field(None, description="Дата поездки (конец диапазона)")
    
    # Фильтры по цене
    min_price: float | None = Field(None, ge=0, description="Минимальная цена за место")
    max_price: float | None = Field(None, ge=0, description="Максимальная цена за место")
    
    # Фильтры по времени
    departure_time_start: time | None = Field(None, description="Время отправления (начало диапазона)")
    departure_time_end: time | None = Field(None, description="Время отправления (конец диапазона)")
    
    # Фильтры по водителю
    driver_rating_min: float | None = Field(None, ge=0, le=5, description="Минимальный рейтинг водителя")
    
    # Фильтры по параметрам поездки
    smoking_allowed: bool | None = Field(None, description="Разрешено ли курение")
    luggage_allowed: bool | None = Field(None, description="Разрешен ли багаж")
    pets_allowed: bool | None = Field(None, description="Разрешены ли животные")
    music_allowed: bool | None = Field(None, description="Разрешена ли музыка")

    # Исключение поездок (на которые уже поданы заявки)
    exclude_trip_ids: list[str] | None = Field(None, description="ID поездок для исключения из поиска")
    
    # Сортировка
    sort_by: str = Field("departure_time", description="Поле для сортировки")
    sort_order: str = Field("asc", description="Направление сортировки")
    
    # Пагинация
    page: int = Field(1, ge=1, description="Номер страницы")
    page_size: int = Field(10, ge=1, le=50, description="Количество записей на странице")

    @model_validator(mode="after")
    def validate_filters(self) -> "TripSearchFilters":
        """Валидация фильтров."""
        # Ограничение page_size максимумом
        if self.page_size > MAX_PAGE_SIZE:
            self.page_size = MAX_PAGE_SIZE
        
        # Валидация min_price <= max_price
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price cannot be greater than max_price")
        
        # Валидация sort_by
        if self.sort_by not in ALLOWED_SORT_BY:
            self.sort_by = "departure_time"
        
        # Валидация sort_order
        if self.sort_order not in ALLOWED_SORT_ORDER:
            self.sort_order = "asc"
        
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "title": "TripSearchFilters",
            "description": "Фильтры для поиска поездок",
        }
    )


class DriverInfo(BaseModel):
    """
    Информация о водителе для отображения в поиске поездок.
    """
    id: str = Field(..., description="ID водителя")
    name: str = Field(..., description="Имя водителя")
    rating_average: float = Field(..., ge=0, le=5, description="Средний рейтинг")
    rating_count: int = Field(..., ge=0, description="Количество отзывов")
    avatar_url: str | None = Field(None, description="URL аватара")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "title": "DriverInfo",
            "description": "Информация о водителе",
        }
    )


class TripSearchResponse(BaseModel):
    """
    Схема ответа для поездки в поиске.
    
    Расширенная версия TripResponse с информацией о водителе.
    """
    # Идентификаторы
    id: str = Field(..., description="Уникальный идентификатор поездки")
    driver_id: str = Field(..., description="ID водителя")
    
    # Маршрут
    from_city: str = Field(..., description="Город отправления")
    from_address: str | None = Field(None, description="Точный адрес отправления")
    to_city: str = Field(..., description="Город назначения")
    to_address: str | None = Field(None, description="Точный адрес назначения")
    
    # Время
    departure_date: str = Field(..., description="Дата поездки")
    departure_time_start: str = Field(..., description="Время отправления")
    departure_time_end: str | None = Field(None, description="Время отправления (конец)")
    is_time_range: bool = Field(..., description="Используется ли диапазон времени")
    arrival_time: str | None = Field(None, description="Ориентировочное время прибытия")
    
    # Цена и вместимость
    price_per_seat: float = Field(..., description="Цена за одно место")
    total_seats: int = Field(..., description="Всего мест")
    available_seats: int = Field(..., description="Доступные места")
    
    # Описание и параметры
    description: str | None = Field(None, description="Описание поездки")
    luggage_allowed: bool = Field(..., description="Разрешён багаж")
    smoking_allowed: bool = Field(..., description="Разрешено курение")
    music_allowed: bool = Field(..., description="Разрешена музыка")
    pets_allowed: bool = Field(..., description="Разрешены животные")
    
    # Информация об автомобиле
    car_model: str | None = Field(None, description="М��дель автомобиля")
    car_color: str | None = Field(None, description="Цвет автомобиля")
    car_license_plate: str | None = Field(None, description="Номерной знак")
    
    # Статус
    status: str = Field(..., description="Статус поездки")
    
    # Информация о водителе
    driver: DriverInfo = Field(..., description="Информация о водителе")
    
    # Служебные поля
    created_at: str = Field(..., description="Время создания")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "title": "TripSearchResponse",
            "description": "Схема ответа для поездки в поиске",
        }
    )


class PaginatedTripSearchResponse(BaseModel):
    """
    Схема для ответа с пагинированным списком поездок при поиске.
    """
    items: list[TripSearchResponse] = Field(..., description="Список найденных поездок")
    total: int = Field(..., description="Общее количество поездок")
    page: int = Field(..., description="Номер текущей страницы")
    page_size: int = Field(..., description="Количество элементов на странице")
    pages: int = Field(..., description="Общее количество страниц")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "title": "PaginatedTripSearchResponse",
            "description": "Пагинированный список найденных поездок",
        }
    )


class TripCreateRequest(BaseModel):
    """
    Схема для создания новой поездки.
    
    Включает обязательные и необязательные поля для создания поездки.
    """
    # Маршрут (обязательные)
    from_city: str = Field(..., min_length=1, max_length=100, description="Город отправления")
    from_address: str | None = Field(None, max_length=255, description="Точный адрес отправления")
    to_city: str = Field(..., min_length=1, max_length=100, description="Город назначения")
    to_address: str | None = Field(None, max_length=255, description="Точный адрес назначения")
    
    # Время (обязательные)
    departure_date: date = Field(..., description="Дата поездки")
    departure_time_start: str = Field(..., pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Время отправления (начало)")
    departure_time_end: str | None = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Время отправления (конец диапазона)")
    is_time_range: bool = Field(default=False, description="Используется ли диапазон времени")
    arrival_time: str | None = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Ориентировочное время прибытия")
    
    # Цена и вместимость (обязательные)
    price_per_seat: float = Field(..., gt=0, description="Цена за одно место")
    total_seats: int = Field(..., ge=1, le=8, description="Всего мест в автомобиле")
    
    # Описание и параметры (необязательные)
    description: str | None = Field(None, max_length=2000, description="Описание поездки")
    luggage_allowed: bool = Field(default=True, description="Разрешён багаж")
    smoking_allowed: bool = Field(default=False, description="Разрешено курение")
    music_allowed: bool = Field(default=True, description="Разрешена музыка")
    pets_allowed: bool = Field(default=False, description="Разрешены животные")
    
    # Информация об автомобиле (необязательные)
    car_model: str | None = Field(None, max_length=100, description="Модель автомобиля")
    car_color: str | None = Field(None, max_length=50, description="Цвет автомобиля")
    car_license_plate: str | None = Field(None, max_length=20, description="Номерной знак")
    
    # Статус (необязательный, по умолчанию draft)
    status: str | None = Field("draft", pattern=r"^(draft|published)$")

    @field_validator("departure_time_start", "departure_time_end", "arrival_time", mode="before")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        """Валидация формата времени HH:MM."""
        if v is not None and isinstance(v, str):
            # Убираем секунды если есть
            if ":" in v and len(v.split(":")) > 2:
                v = v[:5]
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "title": "TripCreateRequest",
            "description": "Схема для создания новой поездки",
        }
    )


class TripUpdateRequest(BaseModel):
    """
    Схема для обновления поездки.
    
    Поддерживает частичное обновление полей.
    """
    # Маршрут
    from_city: str | None = Field(None, min_length=1, max_length=100, description="Город отправления")
    from_address: str | None = Field(None, max_length=255, description="Точный адрес отправления")
    to_city: str | None = Field(None, min_length=1, max_length=100, description="Город назначения")
    to_address: str | None = Field(None, max_length=255, description="Точный адрес назначения")
    
    # Время
    departure_date: date | None = Field(None, description="Дата поездки")
    departure_time_start: str | None = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Время отправления")
    departure_time_end: str | None = Field(None, description="Время отправления (конец диапазона)")
    is_time_range: bool | None = Field(None, description="Используется ли диапазон времени")
    arrival_time: str | None = Field(None, description="Ориентировочное время прибытия")
    
    # Цена и вместимость
    price_per_seat: float | None = Field(None, gt=0, description="Цена за одно место")
    total_seats: int | None = Field(None, ge=1, le=8, description="Всего мест в автомобиле")
    
    # Описание и параметры
    description: str | None = Field(None, max_length=2000, description="Описание поездки")
    luggage_allowed: bool | None = Field(None, description="Разрешён багаж")
    smoking_allowed: bool | None = Field(None, description="Разрешено курение")
    music_allowed: bool | None = Field(None, description="Разрешена музыка")
    pets_allowed: bool | None = Field(None, description="Разрешены животные")
    
    # Информация об автомобиле
    car_model: str | None = Field(None, max_length=100, description="Модель автомобиля")
    car_color: str | None = Field(None, max_length=50, description="Цвет автомобиля")
    car_license_plate: str | None = Field(None, max_length=20, description="Номерной знак")
    
    # Статус
    status: str | None = Field(None, pattern=r"^(draft|published|active|completed|cancelled)$")

    model_config = ConfigDict(
        json_schema_extra={
            "title": "TripUpdateRequest",
            "description": "Схема для обновления поездки",
        }
    )


class TripResponse(BaseModel):
    """
    Схема ответа с данными поездки.
    
    Используется для возврата данных поездки в API.
    """
    # Идентификаторы
    id: str = Field(..., description="Уникальный идентификатор поездки")
    driver_id: str = Field(..., description="ID водителя")
    
    # Маршрут
    from_city: str = Field(..., description="Город отправления")
    from_address: str | None = Field(None, description="Точный адрес отправления")
    to_city: str = Field(..., description="Город назначения")
    to_address: str | None = Field(None, description="Точный адрес назначения")
    
    # Время
    departure_date: str = Field(..., description="Дата поездки")
    departure_time_start: str = Field(..., description="Время отправления")
    departure_time_end: str | None = Field(None, description="Время отправления (конец)")
    is_time_range: bool = Field(..., description="Используется ли диапазон времени")
    arrival_time: str | None = Field(None, description="Ориентировочное время прибытия")
    
    # Цена и вместимость
    price_per_seat: float = Field(..., description="Цена за одно место")
    total_seats: int = Field(..., description="Всего мест")
    available_seats: int = Field(..., description="Доступные места")
    
    # Описание и параметры
    description: str | None = Field(None, description="Описание поездки")
    luggage_allowed: bool = Field(..., description="Разрешён багаж")
    smoking_allowed: bool = Field(..., description="Разрешено курение")
    music_allowed: bool = Field(..., description="Разрешена музыка")
    pets_allowed: bool = Field(..., description="Разрешены животные")
    
    # Информация об автомобиле
    car_model: str | None = Field(None, description="Модель автомобиля")
    car_color: str | None = Field(None, description="Цвет автомобиля")
    car_license_plate: str | None = Field(None, description="Номерной знак")
    
    # Статус
    status: str = Field(..., description="Статус поездки")
    cancelled_at: str | None = Field(None, description="Время отмены")
    cancelled_reason: str | None = Field(None, description="Причина отмены")
    
    # Служебные поля
    created_at: str = Field(..., description="Время создания")
    updated_at: str = Field(..., description="Время последнего обновления")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "title": "TripResponse",
            "description": "Схема ответа с данными поездки",
        }
    )

    @classmethod
    def from_orm(cls, trip: Any) -> "TripResponse":
        """
        Создание схемы из ORM модели.
        
        Args:
            trip: ORM модель поездки
            
        Returns:
            TripResponse: Схема ответа
        """
        return cls(
            id=str(trip.id),
            driver_id=str(trip.driver_id),
            from_city=trip.from_city,
            from_address=trip.from_address,
            to_city=trip.to_city,
            to_address=trip.to_address,
            departure_date=trip.departure_date.isoformat() if hasattr(trip.departure_date, 'isoformat') else str(trip.departure_date),
            departure_time_start=str(trip.departure_time_start) if trip.departure_time_start else "",
            departure_time_end=str(trip.departure_time_end) if trip.departure_time_end else None,
            is_time_range=trip.is_time_range,
            arrival_time=str(trip.arrival_time) if trip.arrival_time else None,
            price_per_seat=float(trip.price_per_seat),
            total_seats=trip.total_seats,
            available_seats=trip.available_seats,
            description=trip.description,
            luggage_allowed=trip.luggage_allowed,
            smoking_allowed=trip.smoking_allowed,
            music_allowed=trip.music_allowed,
            pets_allowed=trip.pets_allowed,
            car_model=trip.car_model,
            car_color=trip.car_color,
            car_license_plate=trip.car_license_plate,
            status=trip.status.value if hasattr(trip.status, 'value') else str(trip.status),
            cancelled_at=trip.cancelled_at.isoformat() if trip.cancelled_at else None,
            cancelled_reason=trip.cancelled_reason,
            created_at=trip.created_at.isoformat() if trip.created_at else "",
            updated_at=trip.updated_at.isoformat() if trip.updated_at else "",
        )


class TripCancelRequest(BaseModel):
    """
    Схема для отмены поездки.
    """
    reason: str | None = Field(None, max_length=500, description="Причина отмены")

    model_config = ConfigDict(
        json_schema_extra={
            "title": "TripCancelRequest",
            "description": "Схема для отмены поездки",
        }
    )


class PaginatedTrips(BaseModel):
    """
    Схема для ответа с пагинированным списком поездок.
    """
    total: int = Field(..., description="Общее количество поездок")
    page: int = Field(..., description="Номер текущей страницы")
    limit: int = Field(..., description="Количество элементов на странице")
    items: list[TripResponse] = Field(..., description="Список поездок")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "title": "PaginatedTrips",
            "description": "Пагинированный список поездок",
        }
    )
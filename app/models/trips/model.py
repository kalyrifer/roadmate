"""
Модель поездки (Trip) для сервиса совместных поездок RoadMate.

Поездка — основная бизнес-сущность системы. Создаётся пользователем (водителем)
и может быть забронирована другими пользователями (пассажирами).
"""
import uuid
from datetime import date, datetime, time
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TripStatus(str, PyEnum):
    """Статусы поездки."""
    DRAFT = "draft"           # Черновик, не опубликована
    PUBLISHED = "published"  # Опубликована, доступна для бронирования
    ACTIVE = "active"         # Активна (в процессе)
    COMPLETED = "completed"   # Завершена
    CANCELLED = "cancelled"   # Отменена


class Trip(Base):
    """Модель поездки."""

    __tablename__ = "trips"

    # === Основные идентификаторы ===
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор поездки",
    )

    # === Связь с водителем ===
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",  # При удалении водителя поездка сохраняется
        ),
        nullable=False,
        index=True,
        comment="ID водителя (создателя поездки)",
    )

    # === Маршрут ===
    from_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Город отправления",
    )
    from_address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Точный адрес отправления",
    )
    to_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Город назначения",
    )
    to_address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Точный адрес назначения",
    )

    # === Время ===
    departure_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Дата поездки",
    )
    departure_time_start: Mapped[time] = mapped_column(
        Time(timezone=True),
        nullable=False,
        comment="Время отправления (начало)",
    )
    departure_time_end: Mapped[time | None] = mapped_column(
        Time(timezone=True),
        nullable=True,
        comment="Время отправления (конец диапазона)",
    )
    is_time_range: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Используется ли диапазон времени",
    )
    arrival_time: Mapped[time | None] = mapped_column(
        Time(timezone=True),
        nullable=True,
        comment="Ориентировочное время прибытия",
    )

    # === Цена и вместимость ===
    price_per_seat: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        index=True,
        comment="Цена за одно место",
    )
    total_seats: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Всего мест в автомобиле",
    )
    available_seats: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Доступные места",
    )

    # === Описание и параметры ===
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Описание поездки",
    )
    luggage_allowed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Разрешён багаж",
    )
    smoking_allowed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Разрешено курение",
    )
    music_allowed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Разрешена музыка",
    )
    pets_allowed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Разрешены животные",
    )

    # === Информация об автомобиле ===
    car_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Модель автомобиля",
    )
    car_color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Цвет автомобиля",
    )
    car_license_plate: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Номерной знак",
    )

    # === Статус ===
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus),
        nullable=False,
        default=TripStatus.DRAFT,
        index=True,
        comment="Статус поездки",
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время отмены",
    )
    cancelled_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Причина отмены",
    )

    # === Служебные поля ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Время создания",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Время последнего обновления",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Время мягкого удаления",
    )

    # === Связи (Relationships) ===

    # Водитель (создатель поездки)
    driver: Mapped["User"] = relationship(
        "User",
        back_populates="trips_as_driver",
        foreign_keys=[driver_id],
    )

    # Заявки на бронирование
    trip_requests: Mapped[list["TripRequest"]] = relationship(
        "TripRequest",
        back_populates="trip",
        cascade="all, delete-orphan",
    )

    # Диалоги, связанные с поездкой
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="trip",
        foreign_keys="Conversation.trip_id",
    )

    # Отзывы о поездке
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="trip",
        foreign_keys="Review.trip_id",
    )

    # === Индексы ===
    __table_args__ = (
        # Основные индексы для поиска
        Index("ix_trips_driver_id", "driver_id"),
        Index("ix_trips_from_city", "from_city"),
        Index("ix_trips_to_city", "to_city"),
        Index("ix_trips_departure_date", "departure_date"),
        Index("ix_trips_status", "status"),
        Index("ix_trips_price_per_seat", "price_per_seat"),
        Index("ix_trips_available_seats", "available_seats"),
        Index("ix_trips_deleted_at", "deleted_at"),
        # Составной индекс для главного поиска поездок
        Index(
            "ix_trips_route_search",
            "from_city",
            "to_city",
            "departure_date",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Trip(id={self.id}, from={self.from_city}, to={self.to_city}, date={self.departure_date})>"


# Импорты для избежания циклических зависимостей
from app.models.users.model import User  # noqa: E402
from app.models.requests import TripRequest  # noqa: E402
from app.models.chat import Conversation  # noqa: E402
from app.models.reviews import Review  # noqa: E402
from app.models.chat import Conversation  # noqa: E402
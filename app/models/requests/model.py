"""
Модель заявки на бронирование (TripRequest) для сервиса совместных поездок RoadMate.

Заявка создаётся пассажиром и привязывается к конкретной поездке.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TripRequestStatus(str, PyEnum):
    """Статусы заявки на бронирование."""
    PENDING = "pending"       # Ожидает решения
    CONFIRMED = "confirmed"   # Подтверждена водителем
    REJECTED = "rejected"     # Отклонена водителем
    CANCELLED = "cancelled"   # Отменена пассажиром


class TripRequest(Base):
    """Модель заявки на бронирование."""

    __tablename__ = "trip_requests"

    # === Основные идентификаторы ===
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор заявки",
    )

    # === Связи с поездкой и пассажиром ===
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "trips.id",
            ondelete="CASCADE",  # При удалении поездки удаляются заявки
        ),
        nullable=False,
        index=True,
        comment="ID поездки",
    )
    passenger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",  # При удалении пассажира удаляются заявки
        ),
        nullable=False,
        index=True,
        comment="ID пассажира",
    )

    # === Данные заявки ===
    seats_requested: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Количество запрашиваемых мест",
    )
    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Сообщение пассажира водителю",
    )

    # === Статус ===
    status: Mapped[TripRequestStatus] = mapped_column(
        Enum(TripRequestStatus),
        nullable=False,
        default=TripRequestStatus.PENDING,
        index=True,
        comment="Статус заявки",
    )

    # === Временные метки ===
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время подтверждения",
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время отклонения",
    )
    rejected_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Причина отклонения",
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время отмены",
    )
    cancelled_by: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Кем отменена: passenger, driver, admin",
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

    # Поездка
    trip: Mapped["Trip"] = relationship(
        "Trip",
        back_populates="trip_requests",
    )

    # Пассажир
    passenger: Mapped["User"] = relationship(
        "User",
        back_populates="trip_requests",
    )

    # === Индексы ===
    __table_args__ = (
        Index("ix_trip_requests_trip_id", "trip_id"),
        Index("ix_trip_requests_passenger_id", "passenger_id"),
        Index("ix_trip_requests_status", "status"),
        Index("ix_trip_requests_deleted_at", "deleted_at"),
        Index("ix_trip_requests_created_at", "created_at"),
        # Уникальный индекс: один пассажир - одна активная заявка на поездку
        Index(
            "ix_trip_requests_unique_active",
            "trip_id",
            "passenger_id",
            unique=True,
            postgresql_where=(status == TripRequestStatus.PENDING),
        ),
    )

    def __repr__(self) -> str:
        return f"<TripRequest(id={self.id}, trip_id={self.trip_id}, passenger_id={self.passenger_id}, status={self.status})>"


from app.models.trips.model import Trip  # noqa: E402
from app.models.users.model import User  # noqa: E402
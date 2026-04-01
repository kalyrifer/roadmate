"""
Repository слой для работы с заявками на бронирование (TripRequest).
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requests.model import TripRequest, TripRequestStatus
from app.models.trips.model import Trip


class TripRequestRepository:
    """Repository для работы с заявками на бронирование."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, trip_id: UUID, passenger_id: UUID, seats_requested: int, message: Optional[str] = None) -> TripRequest:
        """Создание новой заявки."""
        request = TripRequest(
            trip_id=trip_id,
            passenger_id=passenger_id,
            seats_requested=seats_requested,
            message=message,
            status=TripRequestStatus.PENDING,
        )
        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def get_by_id(self, request_id: UUID) -> Optional[TripRequest]:
        """Получение заявки по ID."""
        result = await self.session.execute(
            select(TripRequest)
            .where(
                and_(
                    TripRequest.id == request_id,
                    TripRequest.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, request_id: UUID) -> Optional[TripRequest]:
        """Получение заявки по ID с блокировкой для обновления."""
        result = await self.session.execute(
            select(TripRequest)
            .where(
                and_(
                    TripRequest.id == request_id,
                    TripRequest.deleted_at.is_(None)
                )
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_trip_and_passenger(self, trip_id: UUID, passenger_id: UUID) -> Optional[TripRequest]:
        """Получение заявки по поездке и пассажиру."""
        result = await self.session.execute(
            select(TripRequest)
            .where(
                and_(
                    TripRequest.trip_id == trip_id,
                    TripRequest.passenger_id == passenger_id,
                    TripRequest.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_by_trip_and_passenger(self, trip_id: UUID, passenger_id: UUID) -> Optional[TripRequest]:
        """Получение активной заявки (pending) по поездке и пассажиру."""
        result = await self.session.execute(
            select(TripRequest)
            .where(
                and_(
                    TripRequest.trip_id == trip_id,
                    TripRequest.passenger_id == passenger_id,
                    TripRequest.status == TripRequestStatus.PENDING,
                    TripRequest.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_trip(
        self,
        trip_id: UUID,
        status: Optional[TripRequestStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TripRequest], int]:
        """Получение списка заявок для поездки."""
        conditions = [
            TripRequest.trip_id == trip_id,
            TripRequest.deleted_at.is_(None),
        ]
        if status:
            conditions.append(TripRequest.status == status)

        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(TripRequest.id))
            .where(and_(*conditions))
        )
        total = count_result.scalar()

        # Получаем заявки
        result = await self.session.execute(
            select(TripRequest)
            .where(and_(*conditions))
            .order_by(TripRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        requests = list(result.scalars().all())

        return requests, total

    async def list_by_passenger(
        self,
        passenger_id: UUID,
        status: Optional[TripRequestStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TripRequest], int]:
        """Получение списка заявок пассажира."""
        conditions = [
            TripRequest.passenger_id == passenger_id,
            TripRequest.deleted_at.is_(None),
        ]
        if status:
            conditions.append(TripRequest.status == status)

        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(TripRequest.id))
            .where(and_(*conditions))
        )
        total = count_result.scalar()

        # Получаем заявки
        result = await self.session.execute(
            select(TripRequest)
            .where(and_(*conditions))
            .order_by(TripRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        requests = list(result.scalars().all())

        return requests, total

    async def list_by_driver(
        self,
        driver_id: UUID,
        status: Optional[TripRequestStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TripRequest], int]:
        """Получение списка заявок на поездки водителя."""
        conditions = [
            TripRequest.deleted_at.is_(None),
            # Подзапрос: поездки водителя
            TripRequest.trip_id.in_(
                select(Trip.id).where(Trip.driver_id == driver_id)
            ),
        ]
        if status:
            conditions.append(TripRequest.status == status)

        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(TripRequest.id))
            .where(and_(*conditions))
        )
        total = count_result.scalar()

        # Получаем заявки
        result = await self.session.execute(
            select(TripRequest)
            .where(and_(*conditions))
            .order_by(TripRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        requests = list(result.scalars().all())

        return requests, total

    async def confirm(self, request_id: UUID) -> Optional[TripRequest]:
        """Подтверждение заявки."""
        from datetime import datetime, timezone
        
        request = await self.get_by_id_for_update(request_id)
        if not request or request.status != TripRequestStatus.PENDING:
            return None

        request.status = TripRequestStatus.CONFIRMED
        request.confirmed_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def reject(self, request_id: UUID, reason: Optional[str] = None) -> Optional[TripRequest]:
        """Отклонение заявки."""
        from datetime import datetime, timezone
        
        request = await self.get_by_id_for_update(request_id)
        if not request or request.status != TripRequestStatus.PENDING:
            return None

        request.status = TripRequestStatus.REJECTED
        request.rejected_at = datetime.now(timezone.utc)
        request.rejected_reason = reason
        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def cancel(self, request_id: UUID, cancelled_by: str) -> Optional[TripRequest]:
        """Отмена заявки."""
        from datetime import datetime, timezone
        
        request = await self.get_by_id_for_update(request_id)
        if not request or request.status != TripRequestStatus.PENDING:
            return None

        request.status = TripRequestStatus.CANCELLED
        request.cancelled_at = datetime.now(timezone.utc)
        request.cancelled_by = cancelled_by
        await self.session.flush()
        await self.session.refresh(request)
        return request
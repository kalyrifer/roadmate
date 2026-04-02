"""
Service слой для работы с заявками на бронирование (TripRequest).
Содержит бизнес-логику и проверки.
"""
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.requests.model import TripRequest, TripRequestStatus
from app.models.trips.model import Trip, TripStatus
from app.repositories.requests.repository import TripRequestRepository
from app.schemas.requests import TripRequestCreate, TripRequestList
from app.services.notifications.service import NotificationEventService

from app.models.users.model import User


class TripRequestServiceError(Exception):
    """Базовый класс для ошибок сервиса заявок."""
    pass


class TripNotFoundError(TripRequestServiceError):
    """Поездка не найдена."""
    pass


class TripNotAvailableError(TripRequestServiceError):
    """Поездка недоступна для бронирования."""
    pass


class TripRequestNotFoundError(TripRequestServiceError):
    """Заявка не найдена."""
    pass


class TripRequestAlreadyExistsError(TripRequestServiceError):
    """Заявка уже существует."""
    pass


class TripRequestAlreadyProcessedError(TripRequestServiceError):
    """Заявка уже обработана."""
    pass


class InsufficientSeatsError(TripRequestServiceError):
    """Недостаточно мест."""
    pass


class ForbiddenError(TripRequestServiceError):
    """Нет прав доступа."""
    pass


class CannotBookOwnTripError(TripRequestServiceError):
    """Нельзя забронировать свою поездку."""
    pass


class InvalidStatusTransitionError(TripRequestServiceError):
    """Недопустимый переход статуса."""
    pass


class TripRequestService:
    """Service для работы с заявками на бронирование."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TripRequestRepository(session)
        self.notifications = NotificationEventService(session)

    def _format_user_name(self, user: User | None) -> str:
        if not user:
            return ""
        name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        return name or getattr(user, "email", "") or str(user.id)

    async def _load_request_context(self, request_id: UUID) -> TripRequest:
        """
        Загружает заявку вместе с поездкой, водителем и пассажиром.
        Нужно для корректного формирования уведомлений.
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            select(TripRequest)
            .options(
                selectinload(TripRequest.trip).selectinload(Trip.driver),
                selectinload(TripRequest.passenger),
            )
            .where(
                TripRequest.id == request_id,
                TripRequest.deleted_at.is_(None),
            )
        )
        request = result.scalar_one_or_none()
        if not request:
            raise TripRequestNotFoundError("Заявка не найдена")
        return request

    async def create_request(
        self,
        trip_id: UUID,
        passenger_id: UUID,
        data: TripRequestCreate,
    ) -> TripRequest:
        """Создание заявки на бронирование."""
        # Получаем поездку
        from sqlalchemy import select
        result = await self.session.execute(
            select(Trip).where(Trip.id == trip_id)
        )
        trip = result.scalar_one_or_none()

        if not trip:
            raise TripNotFoundError("Поездка не найдена")

        # Проверка: поездка доступна для бронирования
        if trip.status not in [TripStatus.PUBLISHED, TripStatus.ACTIVE]:
            raise TripNotAvailableError("Поездка недоступна для бронирования")

        # Проверка: пассажир не является водителем
        if trip.driver_id == passenger_id:
            raise CannotBookOwnTripError("Нельзя подать заявку на свою поездку")

        # Проверка: достаточно мест
        if trip.available_seats < data.seats_requested:
            raise InsufficientSeatsError(
                f"Доступно мест: {trip.available_seats}, запрошено: {data.seats_requested}"
            )

        # Проверка: нет активной заявки (pending или confirmed)
        existing_request = await self.repository.get_active_by_trip_and_passenger(
            trip_id, passenger_id
        )
        if existing_request:
            if existing_request.status == TripRequestStatus.CONFIRMED:
                raise TripRequestAlreadyExistsError("У вас уже есть подтверждённая заявка на эту поездку")
            raise TripRequestAlreadyExistsError("У вас уже есть активная заявка на эту поездку")

        # Создаём заявку
        request = await self.repository.create(
            trip_id=trip_id,
            passenger_id=passenger_id,
            seats_requested=data.seats_requested,
            message=data.message,
        )

        # Уведомляем водителя о новой заявке
        try:
            passenger_name = ""
            passenger_result = await self.session.execute(
                select(User).where(User.id == passenger_id)
            )
            passenger = passenger_result.scalar_one_or_none()
            passenger_name = self._format_user_name(passenger)

            await self.notifications.notify_new_request(
                driver_id=trip.driver_id,
                passenger_name=passenger_name,
                trip_id=trip_id,
                request_id=request.id,
                from_city=trip.from_city,
                to_city=trip.to_city,
            )
        except Exception as e:
            # Логируем ошибку уведомления, но не прерываем бронирование
            import logging
            logging.warning(f"Failed to send notification: {e}")

        return request

    async def get_request(self, request_id: UUID) -> TripRequest:
        """Получение заявки по ID."""
        request = await self.repository.get_by_id(request_id)
        if not request:
            raise TripRequestNotFoundError("Заявка не найдена")
        return request

    async def get_trip_requests(
        self,
        trip_id: UUID,
        status_filter: Optional[TripRequestStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TripRequestList:
        """Получение списка заявок для поездки."""
        offset = (page - 1) * page_size
        requests, total = await self.repository.list_by_trip(
            trip_id=trip_id,
            status=status_filter,
            limit=page_size,
            offset=offset,
        )
        
        pages = (total + page_size - 1) // page_size
        
        return TripRequestList(
            items=requests,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_my_requests(
        self,
        passenger_id: UUID,
        status_filter: Optional[TripRequestStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TripRequestList:
        """Получение списка заявок пассажира."""
        offset = (page - 1) * page_size
        requests, total = await self.repository.list_by_passenger(
            passenger_id=passenger_id,
            status=status_filter,
            limit=page_size,
            offset=offset,
        )
        
        pages = (total + page_size - 1) // page_size
        
        return TripRequestList(
            items=requests,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_driver_requests(
        self,
        driver_id: UUID,
        status_filter: Optional[TripRequestStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TripRequestList:
        """Получение списка заявок на поездки водителя."""
        offset = (page - 1) * page_size
        requests, total = await self.repository.list_by_driver(
            driver_id=driver_id,
            status=status_filter,
            limit=page_size,
            offset=offset,
        )
        
        pages = (total + page_size - 1) // page_size
        
        return TripRequestList(
            items=requests,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def confirm_request(
        self,
        request_id: UUID,
        driver_id: UUID,
    ) -> TripRequest:
        """
        Подтверждение заявки водителем.
        
        Использует атомарную операцию с блокировкой строк для защиты от гонок.
        """
        # Получаем заявку (без блокировки - для проверки прав)
        request = await self.repository.get_by_id(request_id)
        if not request:
            raise TripRequestNotFoundError("Заявка не найдена")

        # Проверяем права: водитель должен быть владельцем поездки
        trip = request.trip
        if not trip or trip.driver_id != driver_id:
            raise ForbiddenError("Вы не являетесь водителем этой поездки")

        # Проверяем статус
        if request.status != TripRequestStatus.PENDING:
            raise TripRequestAlreadyProcessedError("Заявка уже обработана")

        # Используем атомарную операцию с блокировкой
        confirmed_request = await self.repository.confirm_with_seats(
            request_id=request_id,
            seats_to_reserve=request.seats_requested,
        )
        
        if not confirmed_request:
            # Проверяем причину: недостаточно мест или уже обработана
            # Делаем повторную проверку заявки
            check_request = await self.repository.get_by_id(request_id)
            if check_request:
                if check_request.status != TripRequestStatus.PENDING:
                    raise TripRequestAlreadyProcessedError("Заявка уже обработана")
                # Если заявка still pending, значит не хватает мест
                raise InsufficientSeatsError("Недостаточно доступных мест")
            raise TripRequestNotFoundError("Заявка не найдена")

        # Уведомляем пассажира о подтверждении заявки
        request_ctx = await self._load_request_context(request_id)
        await self.notifications.notify_request_confirmed(
            passenger_id=request_ctx.passenger_id,
            driver_name=self._format_user_name(request_ctx.trip.driver),
            trip_id=request_ctx.trip_id,
            request_id=request_ctx.id,
            from_city=request_ctx.trip.from_city,
            to_city=request_ctx.trip.to_city,
        )

        return confirmed_request

    async def reject_request(
        self,
        trip_id: UUID,
        request_id: UUID,
        driver_id: UUID,
        reason: Optional[str] = None,
    ) -> TripRequest:
        """
        Отклонение заявки водителем.
        
        Проверяет, что:
        - заявка принадлежит указанной поездке
        - водитель является владельцем поездки
        - заявка в статусе pending
        """
        # Получаем заявку
        request = await self.repository.get_by_id(request_id)
        if not request:
            raise TripRequestNotFoundError("Заявка не найдена")
        
        # Проверяем, что заявка принадлежит указанной поездке
        if request.trip_id != trip_id:
            raise TripRequestNotFoundError("Заявка не найдена для этой поездки")

        # Проверяем права: водитель должен быть владельцем поездки
        trip = request.trip
        if not trip or trip.driver_id != driver_id:
            raise ForbiddenError("Вы не являетесь водителем этой поездки")

        # Проверяем статус: можно отклонять только pending заявки
        if request.status != TripRequestStatus.PENDING:
            raise TripRequestAlreadyProcessedError("Заявка уже обработана")

        # Отклоняем заявку
        rejected_request = await self.repository.reject(request_id, reason)
        if not rejected_request:
            raise TripRequestAlreadyProcessedError("Заявка уже обработана")

        # Уведомляем пассажира о отклонении заявки
        request_ctx = await self._load_request_context(request_id)
        await self.notifications.notify_request_rejected(
            passenger_id=request_ctx.passenger_id,
            driver_name=self._format_user_name(request_ctx.trip.driver),
            trip_id=request_ctx.trip_id,
            request_id=request_ctx.id,
            from_city=request_ctx.trip.from_city,
            to_city=request_ctx.trip.to_city,
            reason=reason,
        )

        return rejected_request

    async def cancel_request(
        self,
        request_id: UUID,
        user_id: UUID,
    ) -> TripRequest:
        """Отмена заявки пассажиром."""
        # Получаем заявку
        request = await self.repository.get_by_id(request_id)
        if not request:
            raise TripRequestNotFoundError("Заявка не найдена")

        # Проверяем права: только владелец заявки может отменить
        if request.passenger_id != user_id:
            raise ForbiddenError("Вы не являетесь владельцем этой заявки")

        # Проверяем статус
        if request.status != TripRequestStatus.PENDING:
            raise TripRequestAlreadyProcessedError("Заявка уже обработана")

        # Отменяем заявку
        cancelled_request = await self.repository.cancel(request_id, "passenger")
        if not cancelled_request:
            raise TripRequestAlreadyProcessedError("Заявка уже обработана")

        # Уведомляем водителя об отмене заявки пассажиром
        request_ctx = await self._load_request_context(request_id)
        await self.notifications.notify_request_cancelled(
            user_id=request_ctx.trip.driver_id,
            trip_id=request_ctx.trip_id,
            request_id=request_ctx.id,
            from_city=request_ctx.trip.from_city,
            to_city=request_ctx.trip.to_city,
            cancelled_by="passenger",
        )

        return cancelled_request

    def _check_driver_owns_trip(self, request: TripRequest, driver_id: UUID) -> bool:
        """Проверка, что водитель владеет поездкой."""
        return request.trip and request.trip.driver_id == driver_id

    def _check_passenger_owns_request(self, request: TripRequest, passenger_id: UUID) -> bool:
        """Проверка, что пассажир владеет заявкой."""
        return request.passenger_id == passenger_id
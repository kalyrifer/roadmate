"""
Сервис для работы с поездками.

Содержит бизнес-логику для создания, обновления, отмены и публикации поездок.
"""
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func

from app.models.trips.model import TripStatus
from app.models.users.model import User, UserRole
from app.repositories.trips.repository import TripRepository
from app.repositories.chat.repository import ChatRepository
from app.schemas.trips.schemas import (
    TripResponse,
    PaginatedTrips,
    TripSearchFilters,
    TripSearchResponse,
    PaginatedTripSearchResponse,
    DriverInfo,
    MAX_PAGE_SIZE,
)


class TripService:
    """
    Сервис для работы с поездками.
    
    Обеспечивает бизнес-логику для работы с поездками.
    """
    
    def __init__(self, trip_repository: TripRepository, db=None):
        """
        Инициализация сервиса.
        
        Args:
            trip_repository: Repository для работы с поездками
            db: Опциональная сессия БД для дополнительных запросов
        """
        self.trip_repo = trip_repository
        self._db = db
    
    async def _create_trip_chat(self, trip_id: uuid.UUID, driver_id: uuid.UUID) -> None:
        """Создание группового чата для поездки с водителем."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self._db:
            logger.warning("No db session for creating trip chat")
            return
        
        try:
            chat_repo = ChatRepository(self._db)
            existing = await chat_repo.get_conversation_by_trip(trip_id)
            if existing:
                logger.info(f"Chat already exists for trip {trip_id}")
                return
            
            conversation = await chat_repo.create_conversation(trip_id)
            await chat_repo.add_participant(conversation.id, driver_id)
            await self._db.flush()
            logger.info(f"Created trip chat {conversation.id} for trip {trip_id} with driver {driver_id}")
        except Exception as e:
            logger.error(f"Failed to create trip chat: {e}", exc_info=True)
    
    async def create_trip(
        self,
        current_user: User,
        trip_data: dict[str, Any]
    ) -> TripResponse:
        """
        Создание новой поездки.
        
        Args:
            current_user: Текущий пользователь (водитель)
            trip_data: Данные для создания поездки
            
        Returns:
            TripResponse: Созданная поездка
            
        Raises:
            HTTPException: 403 если пользователь не водитель
        """
        # Обработка времени: если не указан диапазон, делаем end = start
        if not trip_data.get("is_time_range") and trip_data.get("departure_time_start"):
            trip_data["departure_time_end"] = trip_data["departure_time_start"]
        
        # Создаем поездку
        trip = await self.trip_repo.create(trip_data, current_user.id)
        
        await self._create_trip_chat(trip.id, current_user.id)
        
        return TripResponse.from_orm(trip)
    
    async def search_trips(
        self,
        filters: TripSearchFilters
    ) -> PaginatedTripSearchResponse:
        """
        Поиск поездок с фильтрами и пагинацией.
        
        Args:
            filters: Параметры поиска и фильтрации
            
        Returns:
            PaginatedTripSearchResponse: Список найденных поездок с пагинацией
        """
        # Валидация параметров пагинации
        if filters.page < 1:
            filters.page = 1
        if filters.page_size > MAX_PAGE_SIZE:
            filters.page_size = MAX_PAGE_SIZE
        if filters.page_size < 1:
            filters.page_size = 10
        
        # Получаем поездки
        trips, total = await self.trip_repo.search_trips(filters)
        
        # Вычисляем количество страниц
        pages = (total + filters.page_size - 1) // filters.page_size if total > 0 else 0
        
        # Формируем ответ с информацией о водителях
        items = []
        for trip in trips:
            # Информация о водителе
            driver_info = None
            if trip.driver:
                name = f"{trip.driver.first_name} {trip.driver.last_name}".strip()
                if not name:
                    name = trip.driver.email.split("@")[0]
                driver_info = DriverInfo(
                    id=str(trip.driver.id),
                    name=name,
                    rating_average=float(trip.driver.rating_average) if trip.driver.rating_average else 0.0,
                    rating_count=trip.driver.rating_count or 0,
                    avatar_url=trip.driver.avatar_url,
                )
            
            # Формируем ответ для поездки
            trip_response = TripSearchResponse(
                id=str(trip.id),
                driver_id=str(trip.driver_id),
                from_city=trip.from_city,
                from_address=trip.from_address,
                to_city=trip.to_city,
                to_address=trip.to_address,
                departure_date=trip.departure_date.isoformat() if trip.departure_date else "",
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
                driver=driver_info,
                created_at=trip.created_at.isoformat() if trip.created_at else "",
            )
            items.append(trip_response)
        
        return PaginatedTripSearchResponse(
            items=items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=pages,
        )
    
    async def get_trip(self, trip_id: uuid.UUID) -> TripResponse:
        """
        Получение поездки по ID.
        
        Args:
            trip_id: ID поездки
            
        Returns:
            TripResponse: Поездка
            
        Raises:
            HTTPException: 404 если поездка не найдена
        """
        trip = await self.trip_repo.get_by_id(trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        return TripResponse.from_orm(trip)
    
    async def get_trip_detail(self, trip_id: uuid.UUID) -> dict[str, Any]:
        """
        Получение детальной информации о поездке.
        
        Включает:
        - Основные данные поездки
        - Информацию о водителе (имя, рейтинг)
        - Список подтверждённых пассажиров
        - Отзывы о водителе и поездке
        
        Args:
            trip_id: ID поездки
            
        Returns:
            dict: Детальная информация о поездке
            
        Raises:
            HTTPException: 404 если поездка не найдена
        """
        from app.models.requests.model import TripRequest, TripRequestStatus
        from sqlalchemy import func, select
        
        trip = await self.trip_repo.get_by_id_with_driver(trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Формируем ответ
        trip_data = TripResponse.from_orm(trip)

        # Считаем фактически забронированные места по подтверждённым заявкам,
        # чтобы available_seats всегда соответствовал реальному состоянию,
        # даже если хранимое значение разошлось с заявками.
        if self._db is not None:
            booked_seats_result = await self._db.execute(
                select(func.coalesce(func.sum(TripRequest.seats_requested), 0))
                .where(
                    TripRequest.trip_id == trip_id,
                    TripRequest.status == TripRequestStatus.CONFIRMED,
                    TripRequest.deleted_at.is_(None),
                )
            )
            booked_seats = int(booked_seats_result.scalar() or 0)
            derived_available = max(0, trip.total_seats - booked_seats)
            if trip_data.available_seats != derived_available:
                trip_data = trip_data.model_copy(update={"available_seats": derived_available})
        
        # Информация о водителе
        driver_info = None
        if trip.driver:
            # Формируем имя водителя
            driver_name = None
            if trip.driver.first_name or trip.driver.last_name:
                driver_name = f"{trip.driver.first_name or ''} {trip.driver.last_name or ''}".strip()
            if not driver_name:
                driver_name = trip.driver.email.split("@")[0]
            driver_info = {
                "id": str(trip.driver.id),
                "name": driver_name,
                "rating_average": float(trip.driver.rating_average) if trip.driver.rating_average else None,
                "rating_count": trip.driver.rating_count or 0,
                "avatar_url": trip.driver.avatar_url,
            }
        
        # Формируем результат (без пассажиров - они загружаются отдельно)
        result = {
            "trip": trip_data,
            "driver": driver_info,
            "reviews": [],
        }
        
        return result
    
    async def get_trip_passengers(self, trip_id: uuid.UUID) -> list[dict[str, Any]]:
        """
        Получение списка пассажиров поездки (все статусы).
        
        Args:
            trip_id: ID поездки
            
        Returns:
            list: Список пассажиров с их данными
        """
        from app.repositories.requests.repository import TripRequestRepository
        from app.models.requests.model import TripRequestStatus
        
        passengers_info = []
        
        if self._db:
            request_repo = TripRequestRepository(self._db)
            # Получаем все заявки (включая pending)
            requests_list, _ = await request_repo.list_by_trip(
                trip_id,
                limit=50
            )
            
            for req in requests_list:
                passenger = req.passenger
                if passenger:
                    passenger_name = None
                    if passenger.first_name or passenger.last_name:
                        passenger_name = f"{passenger.first_name or ''} {passenger.last_name or ''}".strip()
                    if not passenger_name:
                        passenger_name = passenger.email.split("@")[0]
                    passengers_info.append({
                        "id": str(passenger.id),
                        "name": passenger_name,
                        "seats_requested": req.seats_requested,
                        "avatar_url": passenger.avatar_url,
                        "rating_average": float(passenger.rating_average) if passenger.rating_average else None,
                    })
        
        return passengers_info

    async def get_driver_trips(
        self,
        current_user: User,
        status_filter: str | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "departure_date",
    ) -> PaginatedTrips:
        """
        Получение списка поездок текущего пользователя (водителя).
        
        Args:
            current_user: Текущий пользователь
            status_filter: Фильтр по статусу (optional)
            page: Номер страницы
            limit: Количество элементов на странице
            sort_by: Поле для сортировки (departure_date или created_at)
            
        Returns:
            PaginatedTrips: Список поездок с пагинацией
        """
        # Валидация параметров
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10
        if limit > 100:
            limit = 100
        
        # Проверка статуса
        trip_status = None
        if status_filter:
            try:
                trip_status = TripStatus(status_filter)
            except ValueError:
                pass
        
        # Получаем поездки
        offset = (page - 1) * limit
        trips, total = await self.trip_repo.get_trips_by_driver(
            driver_id=current_user.id,
            status=trip_status,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
        )
        
        # Формируем ответ
        return PaginatedTrips(
            total=total,
            page=page,
            limit=limit,
            items=[TripResponse.from_orm(trip) for trip in trips]
        )
    
    async def get_passenger_trips(
        self,
        current_user: User,
        status_filter: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> PaginatedTrips:
        """
        Получение списка поездок, где пользователь - пассажир.
        
        Args:
            current_user: Текущий пользователь
            status_filter: Фильтр по статусу (optional)
            page: Номер страницы
            limit: Количество элементов на странице
            
        Returns:
            PaginatedTrips: Список поездок с пагинацией
        """
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10
        if limit > 100:
            limit = 100
        
        # Валидация статуса
        trip_status = None
        if status_filter:
            try:
                trip_status = TripStatus(status_filter)
            except ValueError:
                pass
        
        offset = (page - 1) * limit
        trips, total = await self.trip_repo.get_trips_by_passenger(
            passenger_id=current_user.id,
            status=trip_status,
            offset=offset,
            limit=limit,
        )
        
        return PaginatedTrips(
            total=total,
            page=page,
            limit=limit,
            items=[TripResponse.from_orm(trip) for trip in trips]
        )
    
    async def publish_trip(
        self,
        current_user: User,
        trip_id: uuid.UUID
    ) -> TripResponse:
        """
        Публикация поездки (Draft → Published).
        
        Args:
            current_user: Текущий пользователь
            trip_id: ID поездки
            
        Returns:
            TripResponse: Опубликованная поездка
            
        Raises:
            HTTPException: 401 если не авторизован
            HTTPException: 403 если чужая поездка
            HTTPException: 400 если обязательные поля не заполнены
            HTTPException: 400 если поездка уже опубликована
            HTTPException: 404 если поездка не найдена
        """
        trip = await self.trip_repo.get_by_id(trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Проверка прав: только владелец может публиковать
        if trip.driver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to publish this trip"
            )
        
        # Проверка статуса
        if trip.status == TripStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trip is already published"
            )
        
        if trip.status in (TripStatus.CANCELLED, TripStatus.COMPLETED, TripStatus.ACTIVE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot publish trip with status {trip.status.value}"
            )
        
        # Проверка обязательных полей
        if not trip.from_city:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required field 'from_city' is missing"
            )
        if not trip.to_city:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required field 'to_city' is missing"
            )
        if not trip.departure_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required field 'departure_date' is missing"
            )
        if not trip.total_seats or trip.total_seats < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required field 'total_seats' must be at least 1"
            )
        if not trip.price_per_seat or trip.price_per_seat <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required field 'price_per_seat' must be greater than 0"
            )
        
        # Публикуем поездку
        updated_trip = await self.trip_repo.update_status(
            trip,
            TripStatus.PUBLISHED
        )
        
        return TripResponse.from_orm(updated_trip)
    
    async def update_trip(
        self,
        current_user: User,
        trip_id: uuid.UUID,
        update_data: dict[str, Any]
    ) -> TripResponse:
        """
        Обновление поездки.
        
        Args:
            current_user: Текущий пользователь
            trip_id: ID поездки
            update_data: Данные для обновления
            
        Returns:
            TripResponse: Обновленная поездка
            
        Raises:
            HTTPException: 403 если нет прав
            HTTPException: 404 если поездка не найдена
            HTTPException: 400 если поездка в неправильном статусе
        """
        trip = await self.trip_repo.get_by_id(trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Проверка прав: только владелец или админ может редактировать
        is_owner = trip.driver_id == current_user.id
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, 'role') else False
        
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this trip"
            )
        
        # Проверка статуса: нельзя редактировать cancelled или completed
        if trip.status in (TripStatus.CANCELLED, TripStatus.COMPLETED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update trip with status {trip.status.value}"
            )
        
        # Обработка времени: если не указан диапазон, делаем end = start
        if "is_time_range" in update_data and not update_data["is_time_range"]:
            if "departure_time_start" in update_data:
                update_data["departure_time_end"] = update_data["departure_time_start"]
            elif trip.departure_time_start and not trip.departure_time_end:
                update_data["departure_time_end"] = str(trip.departure_time_start)
        
        # Обновляем поездку
        updated_trip = await self.trip_repo.update(trip, update_data)
        
        return TripResponse.from_orm(updated_trip)
    
    async def cancel_trip(
        self,
        current_user: User,
        trip_id: uuid.UUID,
        reason: str | None = None
    ) -> TripResponse:
        """
        Отмена поездки.
        
        Args:
            current_user: Текущий пользователь
            trip_id: ID поездки
            reason: Причина отмены
            
        Returns:
            TripResponse: Отмененная поездка
            
        Raises:
            HTTPException: 403 если нет прав
            HTTPException: 404 если поездка не найдена
            HTTPException: 400 если поездка уже отменена
        """
        trip = await self.trip_repo.get_by_id_with_requests(trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Проверка прав: только владелец или админ может отменить
        is_owner = trip.driver_id == current_user.id
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, 'role') else False
        
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this trip"
            )
        
        # Проверка статуса
        if trip.status == TripStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trip is already cancelled"
            )
        
        # Отменяем поездку
        cancelled_trip = await self.trip_repo.cancel(
            trip, 
            reason=reason,
            cancelled_by=current_user.id
        )
        
        # TODO: Отправить уведомления пассажирам с подтвержденными заявками
        # if trip.trip_requests:
        #     for request in trip.trip_requests:
        #         if request.status == RequestStatus.CONFIRMED:
        #             await notifications_service.create_notification(...)
        
        return TripResponse.from_orm(cancelled_trip)
    
    async def complete_trip(
        self,
        current_user: User,
        trip_id: uuid.UUID
    ) -> TripResponse:
        """
        Завершение поездки.
        
        Args:
            current_user: Текущий пользователь
            trip_id: ID поездки
            
        Returns:
            TripResponse: Завершенная поездка
            
        Raises:
            HTTPException: 403 если нет прав
            HTTPException: 404 если поездка не найдена
            HTTPException: 400 если поездка уже завершена
        """
        trip = await self.trip_repo.get_by_id_with_requests(trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Проверка прав: только владелец может завершить
        if trip.driver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to complete this trip"
            )
        
        # Проверка статуса
        if trip.status == TripStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trip is already completed"
            )
        
        if trip.status == TripStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot complete cancelled trip"
            )
        
        # Обновляем статус на completed
        completed_trip = await self.trip_repo.update(
            trip,
            {"status": TripStatus.COMPLETED.value}
        )
        
        # Отправляем уведомления пассажирам
        from app.services.notifications.service import NotificationService
        
        # Create notification service instance
        notification_service = NotificationService(self.trip_repo.session)
        
        if trip.trip_requests:
            for request in trip.trip_requests:
                if request.status.name == "CONFIRMED" and request.passenger_id:
                    try:
                        await notification_service.notify_trip_completed(
                            user_id=request.passenger_id,
                            trip_id=trip.id,
                            from_city=trip.from_city,
                            to_city=trip.to_city,
                        )
                    except Exception as e:
                        # Log error but continue
                        print(f"Failed to send notification to passenger {request.passenger_id}: {e}")
        
        return TripResponse.from_orm(completed_trip)
    
    async def delete_trip(
        self,
        current_user: User,
        trip_id: uuid.UUID
    ) -> dict[str, str]:
        """
        Удаление поездки (мягкое удаление).
        
        Args:
            current_user: Текущий пользователь
            trip_id: ID поездки
            
        Returns:
            dict: Сообщение об успехе
            
        Raises:
            HTTPException: 403 если нет прав
            HTTPException: 404 если поездка не найдена
        """
        trip = await self.trip_repo.get_by_id(trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Проверка прав: только владелец или админ может удалить
        is_owner = trip.driver_id == current_user.id
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, 'role') else False
        
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this trip"
            )
        
        # Удаляем поездку
        await self.trip_repo.delete(trip_id)
        
        return {"message": "Trip deleted successfully"}
    
    def can_edit_trip(self, user: User, trip_id: uuid.UUID) -> bool:
        """
        Проверка прав на редактирование поездки.
        
        Args:
            user: Пользователь
            trip_id: ID поездки
            
        Returns:
            bool: True если может редактировать
        """
        # Реализация зависит от конкретного случая использования
        return True
    
    def can_cancel_trip(self, user: User, trip_id: uuid.UUID) -> bool:
        """
        Проверка прав на отмену поездки.
        
        Args:
            user: Пользователь
            trip_id: ID поездки
            
        Returns:
            bool: True если может отменить
        """
        # Реализация зависит от конкретного случая использования
        return True
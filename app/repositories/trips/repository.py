"""
Repository для работы с поездками.

Содержит функции для создания, получения, обновления и отмены поездок.
"""
import uuid
from datetime import datetime, time
from typing import Any

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.trips.model import Trip, TripStatus
from app.models.users.model import User
from app.schemas.trips.schemas import TripSearchFilters


class TripRepository:
    """
    Repository для работы с поездками.
    
    Обеспечивает доступ к данным поездок в БД.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация repository.
        
        Args:
            session: Асинхронная сессия БД
        """
        self.session = session
    
    async def create(self, trip_data: dict[str, Any], driver_id: uuid.UUID) -> Trip:
        """
        Создание новой поездки.
        
        Args:
            trip_data: Данные для создания поездки
            driver_id: ID водителя
            
        Returns:
            Trip: Созданная поездка
        """
        trip = Trip(
            driver_id=driver_id,
            from_city=trip_data.get("from_city"),
            from_address=trip_data.get("from_address"),
            to_city=trip_data.get("to_city"),
            to_address=trip_data.get("to_address"),
            departure_date=trip_data.get("departure_date"),
            departure_time_start=trip_data.get("departure_time_start"),
            departure_time_end=trip_data.get("departure_time_end"),
            is_time_range=trip_data.get("is_time_range", False),
            arrival_time=trip_data.get("arrival_time"),
            price_per_seat=trip_data.get("price_per_seat"),
            total_seats=trip_data.get("total_seats"),
            available_seats=trip_data.get("total_seats"),
            description=trip_data.get("description"),
            luggage_allowed=trip_data.get("luggage_allowed", True),
            smoking_allowed=trip_data.get("smoking_allowed", False),
            music_allowed=trip_data.get("music_allowed", True),
            pets_allowed=trip_data.get("pets_allowed", False),
            car_model=trip_data.get("car_model"),
            car_color=trip_data.get("car_color"),
            car_license_plate=trip_data.get("car_license_plate"),
            status=TripStatus(trip_data.get("status", "draft")),
        )
        trip.normalize_times()
        
        self.session.add(trip)
        await self.session.flush()
        await self.session.refresh(trip)
        return trip
    
    async def get_by_id(self, trip_id: uuid.UUID) -> Trip | None:
        """
        Получение поездки по ID.
        
        Args:
            trip_id: ID поездки
            
        Returns:
            Trip | None: Поездка или None
        """
        stmt = select(Trip).where(
            Trip.id == trip_id,
            Trip.deleted_at.is_(None)
        ).options(selectinload(Trip.driver))
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_id_with_requests(self, trip_id: uuid.UUID) -> Trip | None:
        """
        Получение поездки по ID с загруженными заявками.
        
        Args:
            trip_id: ID поездки
            
        Returns:
            Trip | None: Поездка или None
        """
        stmt = select(Trip).where(
            Trip.id == trip_id,
            Trip.deleted_at.is_(None)
        ).options(
            selectinload(Trip.driver),
            selectinload(Trip.trip_requests)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update(self, trip: Trip, update_data: dict[str, Any]) -> Trip:
        """
        Обновление поездки.
        
        Args:
            trip: Поездка для обновления
            update_data: Данные для обновления
            
        Returns:
            Trip: Обновленная поездка
        """
        # Обновляем только предоставленные поля
        for key, value in update_data.items():
            if value is not None and hasattr(trip, key):
                setattr(trip, key, value)
        
        trip.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(trip)
        return trip
    
    async def cancel(
        self, 
        trip: Trip, 
        reason: str | None = None,
        cancelled_by: uuid.UUID | None = None
    ) -> Trip:
        """
        Отмена поездки.
        
        Args:
            trip: Поездка для отмены
            reason: Причина отмены
            cancelled_by: ID пользователя, отменившего поездку
            
        Returns:
            Trip: Отмененная поездка
        """
        trip.status = TripStatus.CANCELLED
        trip.cancelled_at = datetime.utcnow()
        trip.cancelled_reason = reason
        trip.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(trip)
        return trip
    
    async def delete(self, trip_id: uuid.UUID) -> bool:
        """
        Мягкое удаление поездки.
        
        Args:
            trip_id: ID поездки
            
        Returns:
            bool: True если удалено
        """
        stmt = (
            update(Trip)
            .where(Trip.id == trip_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def exists_by_id(self, trip_id: uuid.UUID) -> bool:
        """
        Проверка существования поездки.
        
        Args:
            trip_id: ID поездки
            
        Returns:
            bool: True если существует
        """
        stmt = select(Trip.id).where(
            Trip.id == trip_id,
            Trip.deleted_at.is_(None)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def get_by_id_with_driver(self, trip_id: uuid.UUID) -> Trip | None:
        """
        Получение поездки по ID с загруженным водителем.
        
        Args:
            trip_id: ID поездки
            
        Returns:
            Trip | None: Поездка или None
        """
        stmt = select(Trip).where(
            Trip.id == trip_id,
            Trip.deleted_at.is_(None)
        ).options(
            selectinload(Trip.driver)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_trips_by_driver(
        self,
        driver_id: uuid.UUID,
        status: TripStatus | None = None,
        offset: int = 0,
        limit: int = 10,
        sort_by: str = "departure_date"
    ) -> tuple[list[Trip], int]:
        """
        Получение списка поездок водителя с пагинацией.
        
        Args:
            driver_id: ID водителя
            status: Фильтр по статусу (optional)
            offset: Смещение для пагинации
            limit: Количество записей
            sort_by: Поле для сортировки (departure_date или created_at)
            
        Returns:
            tuple[list[Trip], int]: Список поездок и общее количество
        """
        # Базовый запрос
        conditions = [
            Trip.driver_id == driver_id,
            Trip.deleted_at.is_(None)
        ]
        
        if status:
            conditions.append(Trip.status == status)
        
        # Подсчет общего количества
        count_stmt = select(Trip.id).where(*conditions)
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.all())
        
        # Определение сортировки
        if sort_by == "created_at":
            order_column = Trip.created_at.desc()
        else:
            order_column = Trip.departure_date.asc()
        
        # Получение данных с пагинацией
        stmt = select(Trip).where(*conditions).order_by(order_column).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        trips = result.scalars().all()
        
        return list(trips), total
    
    async def get_trips_by_passenger(
        self,
        passenger_id: uuid.UUID,
        status: TripStatus | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[Trip], int]:
        """
        Получение списка поездок пассажира с пагинацией.
        
        Args:
            passenger_id: ID пассажира
            status: Фильтр по статусу (optional)
            offset: Смещение для пагинации
            limit: Количество записей
            
        Returns:
            tuple[list[Trip], int]: Список поездок и общее количество
        """
        from app.models.requests.model import TripRequest, TripRequestStatus
        
        # Базовый запрос - ищем поездки где пользователь подтверждён как пассажир
        conditions = [
            TripRequest.passenger_id == passenger_id,
            TripRequest.status == TripRequestStatus.CONFIRMED,
            TripRequest.deleted_at.is_(None),
            Trip.id == TripRequest.trip_id,
            Trip.deleted_at.is_(None)
        ]
        
        if status:
            conditions.append(Trip.status == status)
        
        # Подсчет общего количества
        count_stmt = (
            select(Trip.id)
            .join(TripRequest, TripRequest.trip_id == Trip.id)
            .where(*conditions)
        )
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.all())
        
        # Получение данных с пагинацией
        stmt = (
            select(Trip)
            .join(TripRequest, TripRequest.trip_id == Trip.id)
            .where(*conditions)
            .order_by(Trip.departure_date.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        trips = result.scalars().all()
        
        return list(trips), total
    
    async def update_status(self, trip: Trip, new_status: TripStatus) -> Trip:
        """
        Обновление статуса поездки.
        
        Args:
            trip: Поездка для обновления
            new_status: Новый статус
            
        Returns:
            Trip: Обновленная поездка
        """
        trip.status = new_status
        trip.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(trip)
        return trip
    
    async def search_trips(
        self,
        filters: TripSearchFilters
    ) -> tuple[list[Trip], int]:
        """
        Поиск поездок с фильтрами и пагинацией.
        
        Поддерживает:
        - Поиск по городам (case-insensitive, partial)
        - Фильтры по цене, времени, рейтингу водителя
        - Фильтры по параметрам (pets, smoking, luggage)
        - Сортировка
        - Пагинация
        
        Args:
            filters: Параметры поиска и фильтрации
            
        Returns:
            tuple[list[Trip], int]: Список поездок и общее количество
        """
        # Базовые условия: только опубликованные/активные поездки
        conditions = [
            Trip.deleted_at.is_(None),
            or_(Trip.status == TripStatus.PUBLISHED, Trip.status == TripStatus.ACTIVE),
            Trip.available_seats > 0,
        ]
        
        # JOIN с пользователями для фильтрации по рейтингу водителя
        # We'll use a subquery approach for filtering by driver rating
        user_alias = User.__table__.alias("driver_user")
        
        # Поиск по городам (case-insensitive, partial)
        if filters.from_city:
            conditions.append(
                func.lower(Trip.from_city).like(f"%{filters.from_city.lower()}%")
            )
        if filters.to_city:
            conditions.append(
                func.lower(Trip.to_city).like(f"%{filters.to_city.lower()}%")
            )
        
        # Фильтры по дате
        if filters.date is not None:
            conditions.append(Trip.departure_date == filters.date)
        if filters.date_from is not None:
            conditions.append(Trip.departure_date >= filters.date_from)
        if filters.date_to is not None:
            conditions.append(Trip.departure_date <= filters.date_to)
        
        # Фильтры по цене
        if filters.min_price is not None:
            conditions.append(Trip.price_per_seat >= filters.min_price)
        if filters.max_price is not None:
            conditions.append(Trip.price_per_seat <= filters.max_price)
        
        # Фильтры по времени
        if filters.departure_time_start is not None or filters.departure_time_end is not None:
            if filters.departure_time_start and filters.departure_time_end:
                # Диапазон времени: проверяем пересечение интервалов
                # Для точного времени (is_time_range=False): время должно быть в диапазоне
                # Для диапазона (is_time_range=True): интервалы должны пересекаться
                conditions.append(
                    or_(
                        # Точное время: departure_time_start в диапазоне фильтра
                        and_(
                            Trip.is_time_range == False,
                            Trip.departure_time_start >= filters.departure_time_start,
                            Trip.departure_time_start <= filters.departure_time_end
                        ),
                        # Диапазон: интервалы пересекаются
                        and_(
                            Trip.is_time_range == True,
                            Trip.departure_time_start <= filters.departure_time_end,
                            Trip.departure_time_end >= filters.departure_time_start
                        )
                    )
                )
            elif filters.departure_time_start:
                # Только начало диапазона: время >= start
                conditions.append(Trip.departure_time_start >= filters.departure_time_start)
            elif filters.departure_time_end:
                # Только конец диапазона: время <= end
                conditions.append(Trip.departure_time_start <= filters.departure_time_end)
        
        # Фильтры по параметрам поездки
        if filters.smoking_allowed is not None:
            conditions.append(Trip.smoking_allowed == filters.smoking_allowed)
        if filters.luggage_allowed is not None:
            conditions.append(Trip.luggage_allowed == filters.luggage_allowed)
        if filters.pets_allowed is not None:
            conditions.append(Trip.pets_allowed == filters.pets_allowed)
        if filters.music_allowed is not None:
            conditions.append(Trip.music_allowed == filters.music_allowed)
        
        # Исключение поездок, на которые уже поданы заявки
        if filters.exclude_trip_ids:
            from uuid import UUID
            exclude_ids = []
            for tid in filters.exclude_trip_ids:
                try:
                    exclude_ids.append(UUID(tid))
                except ValueError:
                    pass
            print(f"[DEBUG] exclude_trip_ids from filter: {filters.exclude_trip_ids}")
            print(f"[DEBUG] Parsed exclude_ids: {[str(e) for e in exclude_ids]}")
            if exclude_ids:
                conditions.append(Trip.id.not_in(exclude_ids))
        
        # Построение запроса с JOIN для фильтрации по рейтингу
        # Подсчет общего количества
        count_stmt = (
            select(func.count(Trip.id))
            .join(User, Trip.driver_id == User.id)
            .where(and_(*conditions))
        )
        
        # Фильтр по рейтингу водителя (через JOIN)
        if filters.driver_rating_min is not None:
            count_stmt = count_stmt.where(User.rating_average >= filters.driver_rating_min)
        
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Определение сортировки
        sort_column = Trip.departure_date.asc()
        if filters.sort_by == "price":
            sort_column = Trip.price_per_seat.asc() if filters.sort_order == "asc" else Trip.price_per_seat.desc()
        elif filters.sort_by == "departure_time":
            sort_column = Trip.departure_time_start.asc() if filters.sort_order == "asc" else Trip.departure_time_start.desc()
        elif filters.sort_by == "created_at":
            sort_column = Trip.created_at.asc() if filters.sort_order == "asc" else Trip.created_at.desc()
        elif filters.sort_by == "driver_rating":
            # Для сортировки по рейтингу нужен JOIN
            sort_column = User.rating_average.asc() if filters.sort_order == "asc" else User.rating_average.desc()
        
        # Пагинация
        offset = (filters.page - 1) * filters.page_size
        limit = filters.page_size
        
        # Основной запрос с JOIN для загрузки водителя
        stmt = (
            select(Trip)
            .join(User, Trip.driver_id == User.id)
            .where(and_(*conditions))
            .order_by(sort_column)
            .offset(offset)
            .limit(limit)
            .options(selectinload(Trip.driver))
        )
        
        # Фильтр по рейтингу водителя
        if filters.driver_rating_min is not None:
            stmt = stmt.where(User.rating_average >= filters.driver_rating_min)
        
        result = await self.session.execute(stmt)
        trips = result.scalars().all()
        
        return list(trips), total

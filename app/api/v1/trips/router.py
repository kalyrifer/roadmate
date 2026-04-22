
"""
Роутер домена Trips (Поездки).

Эндпоинты:
- POST / — создание поездки
- GET /{trip_id} — детали поездки
- PUT /{trip_id} — редактирование поездки
- DELETE /{trip_id} — отмена поездки
"""
import uuid
from datetime import date, time
from typing import Annotated, Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import CurrentUser, CurrentUserOptional, get_current_user, get_current_user_optional
from app.models.users.model import User
from app.repositories.requests.repository import TripRequestRepository
from app.schemas.trips.schemas import (
    TripCreateRequest,
    TripUpdateRequest,
    TripResponse,
    TripCancelRequest,
    PaginatedTrips,
    TripSearchFilters,
    PaginatedTripSearchResponse,
)
from app.repositories.trips.repository import TripRepository
from app.services.trips.service import TripService

router = APIRouter()


async def get_trip_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TripRepository:
    """
    Получение repository для работы с поездками.
    
    Args:
        db: Сессия БД
        
    Returns:
        TripRepository: Экземпляр repository
    """
    return TripRepository(db)


async def get_request_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TripRequestRepository:
    """
    Получение repository для работы с заявками на поездки.
    
    Args:
        db: Сессия БД
        
    Returns:
        TripRequestRepository: Экземпляр repository
    """
    return TripRequestRepository(db)


async def get_trip_service(
    trip_repository: TripRepository = Depends(get_trip_repository),
    db: AsyncSession = Depends(get_db)
) -> TripService:
    """
    Получение сервиса для работы с поездками.
    
    Args:
        trip_repository: Repository для работы с поездками
        db: Сессия БД
        
    Returns:
        TripService: Экземпляр сервиса
    """
    return TripService(trip_repository, db)


# Типы для зависимостей
TripServiceDep = Annotated[TripService, Depends(get_trip_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
RequestRepoDep = Annotated[TripRequestRepository, Depends(get_request_repository)]
CurrentUserOptDep = Annotated[Union[User, None], Depends(get_current_user_optional)]


@router.get("/", response_model=PaginatedTripSearchResponse)
async def search_trips(
    current_user: CurrentUserOptDep,
    trip_service: TripServiceDep,
    request_repo: RequestRepoDep,
    # Базовый поиск по городам
    from_city: str | None = Query(None, description="Город отправления (частичный поиск)"),
    to_city: str | None = Query(None, description="Город назначения (частичный поиск)"),
    # Фильтры по дате
    date: date | None = Query(None, description="Дата поездки (точное совпадение)"),
    date_from: date | None = Query(None, description="Дата поездки (начало диапазона)"),
    date_to: date | None = Query(None, description="Дата поездки (конец диапазона)"),
    # Фильтры по цене
    min_price: float | None = Query(None, ge=0, description="Минимальная цена за место"),
    max_price: float | None = Query(None, ge=0, description="Максимальная цена за место"),
    # Фильтры по времени
    departure_time_start: time | None = Query(None, description="Время отправления (начало диапазона)"),
    departure_time_end: time | None = Query(None, description="Время отправления (конец диапазона)"),
    # Фильтры по водителю
    driver_rating_min: float | None = Query(None, ge=0, le=5, description="Минимальный рейтинг водителя"),
    # Фильтры по параметрам поездки
    smoking_allowed: bool | None = Query(None, description="Разрешено ли курение"),
    luggage_allowed: bool | None = Query(None, description="Разрешен ли багаж"),
    pets_allowed: bool | None = Query(None, description="Разрешены ли животные"),
    # Сортировка
    sort_by: str = Query("departure_time", description="Поле для сортировки: price, departure_time, created_at, driver_rating"),
    sort_order: str = Query("asc", description="Направление сортировки: asc, desc"),
    # Пагинация
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=50, description="Количество записей на странице"),
) -> PaginatedTripSearchResponse:
    """
    Поиск поездок с фильтрами.
    
    Поддерживает:
    - Базовый поиск по городам (case-insensitive, partial)
    - Фильтры по цене, времени, рейтингу водителя
    - Фильтры по параметрам (pets, smoking, luggage)
    - Сортировка
    - Пагинация
    
    Возвращает только поездки со статусом 'published' или 'active'.
    Исключает поездки, на которые текущий пользователь уже подал заявку.
    """
    # Валидация: min_price не может быть больше max_price
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_price_range",
                "message": "min_price cannot be greater than max_price"
            }
        )
    
    # Получаем ID поездок, на которые пользователь уже подал заявку
    exclude_trip_ids = None
    print(f"[DEBUG search_trips] current_user is None: {current_user is None}")
    if current_user:
        active_trip_ids = await request_repo.get_active_trip_ids_by_passenger(current_user.id)
        print(f"[DEBUG search_trips] User {current_user.id} has {len(active_trip_ids)} active trips")
        if active_trip_ids:
            exclude_trip_ids = [str(tid) for tid in active_trip_ids]
            print(f"[DEBUG search_trips] Will exclude: {exclude_trip_ids}")
    else:
        print("[DEBUG search_trips] No current user - will not exclude any trips")
    
    # Создаем фильтры
    filters = TripSearchFilters(
        from_city=from_city,
        to_city=to_city,
        date=date,
        date_from=date_from,
        date_to=date_to,
        min_price=min_price,
        max_price=max_price,
        departure_time_start=departure_time_start,
        departure_time_end=departure_time_end,
        driver_rating_min=driver_rating_min,
        smoking_allowed=smoking_allowed,
        luggage_allowed=luggage_allowed,
        pets_allowed=pets_allowed,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        exclude_trip_ids=exclude_trip_ids,
    )
    
    return await trip_service.search_trips(filters)


@router.get("/my/driver", response_model=PaginatedTrips)
async def get_my_trips(
    current_user: CurrentUserDep,
    trip_service: TripServiceDep,
    status: str | None = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "departure_date",
) -> PaginatedTrips:
    """
    Получение списка своих поездок (водитель).
    
    Возвращает поездки текущего пользователя с пагинацией.
    
    Args:
        current_user: Текущий авторизованный пользователь
        trip_service: Сервис для работы с поездками
        status: Фильтр по статусу (optional)
        page: Номер страницы
        limit: Количество элементов на странице
        sort_by: Поле для сортировки (departure_date или created_at)
        
    Returns:
        PaginatedTrips: Список поездок с пагинацией
    """
    return await trip_service.get_driver_trips(
        current_user=current_user,
        status_filter=status,
        page=page,
        limit=limit,
        sort_by=sort_by,
    )


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: TripCreateRequest,
    current_user: CurrentUserDep,
    trip_service: TripServiceDep,
) -> TripResponse:
    """
    Создание новой поездки.
    
    Создает новую поездку от имени текущего пользователя (водителя).
    
    Args:
        trip_data: Данные для создания поездки
        current_user: Текущий авторизованный пользователь
        trip_service: Сервис для работы с поездками
        
    Returns:
        TripResponse: Созданная поездка
        
    Raises:
        HTTPException: 403 если пользователь не авторизован
    """
    return await trip_service.create_trip(
        current_user=current_user,
        trip_data=trip_data.model_dump()
    )


@router.get("/{trip_id}")
async def get_trip(
    trip_id: str,
    trip_service: TripServiceDep,
):
    """
    Получение полных деталей поездки с информацией о водителе.
    
    Returns:
        Объект с данными поездки, водителя и отзывов
        
    Raises:
        HTTPException: 400 если неверный формат UUID
        HTTPException: 404 если поездка не найдена
    """
    # Валидация UUID
    try:
        trip_uuid = uuid.UUID(trip_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trip ID format"
        )
    
    return await trip_service.get_trip_detail(trip_uuid)


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    trip_data: TripUpdateRequest,
    current_user: CurrentUserDep,
    trip_service: TripServiceDep,
) -> TripResponse:
    """
    Редактирование поездки.
    
    Обновляет данные поездки. Только владелец поездки или админ может редактировать.
    
    Args:
        trip_id: ID поездки (UUID строка)
        trip_data: Данные для обновления
        current_user: Текущий авторизованный пользователь
        trip_service: Сервис для работы с поездками
        
    Returns:
        TripResponse: Обновленная поездка
        
    Raises:
        HTTPException: 400 если неверный формат UUID
        HTTPException: 403 если нет прав
        HTTPException: 404 если поездка не найдена
        HTTPException: 400 если поездка в неправильном статусе
    """
    # Валидация UUID
    try:
        trip_uuid = uuid.UUID(trip_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trip ID format"
        )
    
    # Фильтруем только не-None значения для обновления
    update_data = {k: v for k, v in trip_data.model_dump().items() if v is not None}
    
    return await trip_service.update_trip(
        current_user=current_user,
        trip_id=trip_uuid,
        update_data=update_data
    )


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_trip(
    trip_id: str,
    current_user: CurrentUserDep,
    trip_service: TripServiceDep,
    reason: str | None = None,
) -> None:
    """
    Отмена поездки.
    
    Отменяет поездку (изменяет статус на cancelled). Только владелец поездки или админ может отменить.
    
    Args:
        trip_id: ID поездки (UUID строка)
        current_user: Текущий авторизованный пользователь
        trip_service: Сервис для работы с поездками
        reason: Причина отмены (query параметр)
        
    Raises:
        HTTPException: 400 если неверный формат UUID
        HTTPException: 403 если нет прав
        HTTPException: 404 если поездка не найдена
        HTTPException: 400 если поездка уже отменена
    """
    # Валидация UUID
    try:
        trip_uuid = uuid.UUID(trip_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trip ID format"
        )
    
    await trip_service.cancel_trip(
        current_user=current_user,
        trip_id=trip_uuid,
        reason=reason
    )


@router.patch("/{trip_id}/publish", response_model=TripResponse)
async def publish_trip(
    trip_id: str,
    current_user: CurrentUserDep,
    trip_service: TripServiceDep,
) -> TripResponse:
    """
    Публикация поездки.
    
    Публикует черновик поездки, делая её доступной для поиска.
    
    Args:
        trip_id: ID поездки (UUID строка)
        current_user: Текущий авторизованный пользователь
        trip_service: Сервис для работы с поездками
        
    Returns:
        TripResponse: Опубликованная поездка
    """
    # Валидация UUID
    try:
        trip_uuid = uuid.UUID(trip_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trip ID format"
        )
    
    return await trip_service.publish_trip(
        current_user=current_user,
        trip_id=trip_uuid
    )


@router.get("/{trip_id}/passengers")
async def get_trip_passengers(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Получение списка пассажиров поездки.
    """
    from app.models.requests.model import TripRequest, TripRequestStatus
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    
    try:
        trip_uuid = uuid.UUID(trip_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trip ID format"
        )
    
    # Get requests with passenger data
    result = await db.execute(
        select(TripRequest)
        .options(joinedload(TripRequest.passenger))
        .where(
            TripRequest.trip_id == trip_uuid,
            TripRequest.status == TripRequestStatus.CONFIRMED,
            TripRequest.deleted_at.is_(None)
        )
        .limit(50)
    )
    requests_list = result.scalars().all()
    
    passengers = []
    for req in requests_list:
        passenger = req.passenger
        if passenger:
            name = None
            if passenger.first_name or passenger.last_name:
                name = f"{passenger.first_name or ''} {passenger.last_name or ''}".strip()
            if not name:
                name = passenger.email.split("@")[0]
            passengers.append({
                "id": str(passenger.id),
                "name": name,
                "seats_requested": req.seats_requested,
                "avatar_url": passenger.avatar_url,
                "rating_average": float(passenger.rating_average) if passenger.rating_average else None,
            })
    
    return passengers
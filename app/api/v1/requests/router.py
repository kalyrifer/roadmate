"""
Роутер для работы с заявками на бронирование (TripRequest).

Эндпоинты:
- POST /trips/{trip_id}/requests - создание заявки
- GET /trips/{trip_id}/requests - список заявок поездки
- GET /requests/my - мои заявки
- GET /requests/driver - заявки на мои поездки
- GET /requests/{request_id} - детали заявки
- POST /requests/{request_id}/confirm - подтверждение
- POST /requests/{request_id}/reject - отклонение
- DELETE /requests/{request_id} - отмена
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentUserId
from app.models.requests.model import TripRequestStatus
from app.schemas.requests import (
    TripRequestCreate,
    TripRequestRead,
    TripRequestList,
    TripRequestAction,
)
from app.services.requests.service import (
    TripRequestService,
    TripNotFoundError,
    TripNotAvailableError,
    TripRequestNotFoundError,
    TripRequestAlreadyExistsError,
    TripRequestAlreadyProcessedError,
    InsufficientSeatsError,
    ForbiddenError,
    CannotBookOwnTripError,
)


router = APIRouter(prefix="/requests", tags=["requests"])


# === Схема ответа об ошибке ===
class ErrorResponse(BaseModel):
    detail: str


# === Создание заявки ===
@router.post(
    "/trips/{trip_id}/requests",
    response_model=TripRequestRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse, "description": "Поездка не найдена"},
        409: {"model": ErrorResponse, "description": "Заявка уже существует"},
        422: {"model": ErrorResponse, "description": "Ошибка валидации"},
    },
)
async def create_request(
    trip_id: UUID,
    data: TripRequestCreate,
    db: DbSession,
    current_user_id: int,
):
    """Создание заявки на бронирование поездки."""
    service = TripRequestService(db)
    
    try:
        request = await service.create_request(
            trip_id=trip_id,
            passenger_id=UUID(int=current_user_id),  # Convert int to UUID
            data=data,
        )
        await db.commit()
        return request
    except TripNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TripNotAvailableError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except CannotBookOwnTripError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except InsufficientSeatsError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except TripRequestAlreadyExistsError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# === Получение списка заявок поездки ===
@router.get(
    "/trips/{trip_id}/requests",
    response_model=TripRequestList,
    responses={
        404: {"model": ErrorResponse, "description": "Поездка не найдена"},
    },
)
async def list_trip_requests(
    trip_id: UUID,
    db: DbSession,
    current_user_id: int,
    status: Optional[TripRequestStatus] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
):
    """Получение списка заявок на бронирование поездки."""
    service = TripRequestService(db)
    
    try:
        result = await service.get_trip_requests(
            trip_id=trip_id,
            status_filter=status,
            page=page,
            page_size=page_size,
        )
        return result
    except TripNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# === Мои заявки (пассажир) ===
@router.get(
    "/my",
    response_model=TripRequestList,
)
async def get_my_requests(
    db: DbSession,
    current_user_id: int,
    status: Optional[TripRequestStatus] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
):
    """Получение списка моих заявок."""
    service = TripRequestService(db)
    
    try:
        result = await service.get_my_requests(
            passenger_id=UUID(int=current_user_id),
            status_filter=status,
            page=page,
            page_size=page_size,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# === Заявки на мои поездки (водитель) ===
@router.get(
    "/driver",
    response_model=TripRequestList,
)
async def get_driver_requests(
    db: DbSession,
    current_user_id: int,
    status: Optional[TripRequestStatus] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
):
    """Получение списка заявок на мои поездки."""
    service = TripRequestService(db)
    
    try:
        result = await service.get_driver_requests(
            driver_id=UUID(int=current_user_id),
            status_filter=status,
            page=page,
            page_size=page_size,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# === Получение одной заявки ===
@router.get(
    "/{request_id}",
    response_model=TripRequestRead,
    responses={
        404: {"model": ErrorResponse, "description": "Заявка не найдена"},
    },
)
async def get_request(
    request_id: UUID,
    db: DbSession,
    current_user_id: int,
):
    """Получение заявки по ID."""
    service = TripRequestService(db)
    
    try:
        request = await service.get_request(request_id)
        
        # Проверка доступа: владелец заявки или водитель поездки
        if request.passenger_id != UUID(int=current_user_id):
            if not request.trip or request.trip.driver_id != UUID(int=current_user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Нет доступа к этой заявке"
                )
        
        return request
    except TripRequestNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# === Подтверждение заявки (водитель) ===
@router.post(
    "/{request_id}/confirm",
    response_model=TripRequestRead,
    responses={
        404: {"model": ErrorResponse, "description": "Заявка не найдена"},
        403: {"model": ErrorResponse, "description": "Нет прав доступа"},
        409: {"model": ErrorResponse, "description": "Заявка уже обработана"},
        422: {"model": ErrorResponse, "description": "Недостаточно мест"},
    },
)
async def confirm_request(
    request_id: UUID,
    db: DbSession,
    current_user_id: int,
):
    """Подтверждение заявки на бронирование (водителем)."""
    service = TripRequestService(db)
    
    try:
        request = await service.confirm_request(
            request_id=request_id,
            driver_id=UUID(int=current_user_id),
        )
        await db.commit()
        return request
    except TripRequestNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InsufficientSeatsError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except TripRequestAlreadyProcessedError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# === Отклонение заявки (водитель) ===
@router.post(
    "/{request_id}/reject",
    response_model=TripRequestRead,
    responses={
        404: {"model": ErrorResponse, "description": "Заявка не найдена"},
        403: {"model": ErrorResponse, "description": "Нет прав доступа"},
        409: {"model": ErrorResponse, "description": "Заявка уже обработана"},
    },
)
async def reject_request(
    request_id: UUID,
    data: Optional[TripRequestAction] = None,
    db: DbSession,
    current_user_id: int,
):
    """Отклонение заявки на бронирование (водителем)."""
    service = TripRequestService(db)
    
    try:
        reason = data.rejected_reason if data else None
        request = await service.reject_request(
            request_id=request_id,
            driver_id=UUID(int=current_user_id),
            reason=reason,
        )
        await db.commit()
        return request
    except TripRequestNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except TripRequestAlreadyProcessedError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# === Отмена заявки (пассажир) ===
@router.delete(
    "/{request_id}",
    response_model=TripRequestRead,
    responses={
        404: {"model": ErrorResponse, "description": "Заявка не найдена"},
        403: {"model": ErrorResponse, "description": "Нет прав доступа"},
        409: {"model": ErrorResponse, "description": "Заявка уже обработана"},
    },
)
async def cancel_request(
    request_id: UUID,
    db: DbSession,
    current_user_id: int,
):
    """Отмена заявки на бронирование (пассажиром)."""
    service = TripRequestService(db)
    
    try:
        request = await service.cancel_request(
            request_id=request_id,
            user_id=UUID(int=current_user_id),
        )
        await db.commit()
        return request
    except TripRequestNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except TripRequestAlreadyProcessedError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
"""
Роутер домена Reviews.
Эндпоинты:
- POST / — создание отзыва
- GET /user/{user_id} — отзывы о пользователе
- GET /trip/{trip_id} — отзывы о поездке
- PUT /{id} — обновление статуса отзыва
- DELETE /{id} — удаление отзыва
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.reviews.model import ReviewStatus
from app.models.users.model import User
from app.schemas.reviews import (
    ReviewCreate,
    ReviewCreateResponse,
    ReviewList,
    ReviewStatusUpdate,
)
from app.services.reviews.service import (
    ReviewService,
    ReviewNotFoundError,
    TripNotFoundError,
    TripNotCompletedError,
    ReviewAlreadyExistsError,
    UserNotParticipantError,
    CannotReviewSelfError,
    ForbiddenError,
)

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewCreateResponse:
    """Создание отзыва (после завершения поездки).
    
    Требования:
    - Поездка должна быть завершена (status=completed)
    - Автор должен быть участником поездки
    - Нельзя оставить отзыв о себе
    - Один пользователь может оставить только один отзыв на поездку
    """
    service = ReviewService(db)
    
    try:
        review = await service.create_review(
            author_id=current_user.id,
            data=data,
        )
        return ReviewCreateResponse.model_validate(review)
    except TripNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except TripNotCompletedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except UserNotParticipantError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except CannotReviewSelfError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ReviewAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/user/{user_id}", response_model=ReviewList)
async def get_user_reviews(
    user_id: UUID,
    status_filter: Optional[ReviewStatus] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewList:
    """Получение отзывов о пользователе.
    
    Поддерживается фильтрация по статусу:
    - published (опубликованные)
    - pending (на модерации)
    - rejected (отклонённые)
    """
    service = ReviewService(db)
    
    return await service.get_user_reviews(
        user_id=user_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get("/trip/{trip_id}", response_model=ReviewList)
async def get_trip_reviews(
    trip_id: UUID,
    status_filter: Optional[ReviewStatus] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewList:
    """Получение отзывов о поездке.
    
    Поддерживается фильтрация по статусу:
    - published (опубликованные)
    - pending (на модерации)
    - rejected (отклонённые)
    """
    service = ReviewService(db)
    
    return await service.get_trip_reviews(
        trip_id=trip_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.put("/{review_id}", response_model=ReviewCreateResponse)
async def update_review_status(
    review_id: UUID,
    data: ReviewStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewCreateResponse:
    """Обновление статуса отзыва (модерация).
    
    Только автор отзыва может изменить статус или администратор.
    """
    service = ReviewService(db)
    
    try:
        review = await service.update_review_status(
            review_id=review_id,
            new_status=data.status,
        )
        return ReviewCreateResponse.model_validate(review)
    except ReviewNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление отзыва.
    
    Только автор отзыва может удалить свой отзыв.
    """
    service = ReviewService(db)
    
    try:
        await service.delete_review(
            review_id=review_id,
            user_id=current_user.id,
        )
    except ReviewNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/me/trip/{trip_id}/can-review")
async def check_can_review(
    trip_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Проверка, может ли текущий пользователь оставить отзыв на поездку."""
    service = ReviewService(db)
    
    can_review, reason = await service.check_user_can_review(
        user_id=current_user.id,
        trip_id=trip_id,
    )
    
    return {
        "can_review": can_review,
        "reason": reason,
    }
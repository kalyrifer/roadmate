"""
Service слой для работы с отзывами (Review).
Содержит бизнес-логику и проверки.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reviews.model import Review, ReviewStatus
from app.models.trips.model import Trip, TripStatus
from app.models.requests.model import TripRequest, TripRequestStatus
from app.repositories.reviews.repository import ReviewRepository
from app.schemas.reviews import ReviewCreate, ReviewList


class ReviewServiceError(Exception):
    """Базовый класс для ошибок сервиса отзывов."""
    pass


class ReviewNotFoundError(ReviewServiceError):
    """Отзыв не найден."""
    pass


class TripNotFoundError(ReviewServiceError):
    """Поездка не найдена."""
    pass


class TripNotCompletedError(ReviewServiceError):
    """Поездка не завершена."""
    pass


class ReviewAlreadyExistsError(ReviewServiceError):
    """Отзыв уже существует."""
    pass


class UserNotParticipantError(ReviewServiceError):
    """Пользователь не является участником поездки."""
    pass


class CannotReviewSelfError(ReviewServiceError):
    """Нельзя оставить отзыв о себе."""
    pass


class ForbiddenError(ReviewServiceError):
    """Нет прав доступа."""
    pass


class ReviewService:
    """Service для работы с отзывами."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ReviewRepository(session)

    async def _get_trip(self, trip_id: UUID) -> Optional[Trip]:
        """Получение поездки по ID."""
        result = await self.session.execute(
            select(Trip).where(Trip.id == trip_id)
        )
        return result.scalar_one_or_none()

    async def _get_confirmed_participants(self, trip_id: UUID) -> set[UUID]:
        """Получение ID подтверждённых участников поездки (водитель + подтверждённые пассажиры)."""
        # Получаем поездку
        trip = await self._get_trip(trip_id)
        if not trip:
            return set()
        
        participants = {trip.driver_id}
        
        # Получаем подтверждённые заявки
        result = await self.session.execute(
            select(TripRequest.passenger_id)
            .where(
                TripRequest.trip_id == trip_id,
                TripRequest.status == TripRequestStatus.CONFIRMED,
                TripRequest.deleted_at.is_(None)
            )
        )
        confirmed_passengers = result.scalars().all()
        participants.update(confirmed_passengers)
        
        return participants

    async def create_review(
        self,
        author_id: UUID,
        data: ReviewCreate,
    ) -> Review:
        """Создание отзыва."""
        # Получаем поездку
        trip = await self._get_trip(data.trip_id)
        if not trip:
            raise TripNotFoundError("Поездка не найдена")

        # Проверка: поездка завершена
        if trip.status != TripStatus.COMPLETED:
            raise TripNotCompletedError("Отзыв можно оставить только после завершения поездки")

        # Проверка: автор не может оставить отзыв о себе
        if author_id == data.target_id:
            raise CannotReviewSelfError("Нельзя оставить отзыв о себе")

        # Проверка: автор является участником поездки
        participants = await self._get_confirmed_participants(data.trip_id)
        if author_id not in participants:
            raise UserNotParticipantError("Вы не являетесь участником этой поездки")

        # Проверка: цель отзыва является участником поездки
        if data.target_id not in participants:
            raise UserNotParticipantError("Пользователь не является участником этой поездки")

        # Проверка: отзыв ещё не существует (защита на уровне БД + проверка)
        existing_review = await self.repository.get_by_trip_and_author(
            data.trip_id, author_id
        )
        if existing_review:
            raise ReviewAlreadyExistsError("Вы уже оставили отзыв на эту поездку")

        # Создаём отзыв
        review = await self.repository.create(
            trip_id=data.trip_id,
            author_id=author_id,
            target_id=data.target_id,
            rating=data.rating,
            text=data.text,
        )

        return review

    async def get_review(self, review_id: UUID) -> Review:
        """Получение отзыва по ID."""
        review = await self.repository.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundError("Отзыв не найден")
        return review

    async def get_trip_reviews(
        self,
        trip_id: UUID,
        status_filter: Optional[ReviewStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ReviewList:
        """Получение списка отзывов для поездки."""
        offset = (page - 1) * page_size
        reviews, total = await self.repository.list_by_trip(
            trip_id=trip_id,
            status=status_filter,
            limit=page_size,
            offset=offset,
        )
        
        pages = (total + page_size - 1) // page_size
        
        return ReviewList(
            items=reviews,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_user_reviews(
        self,
        user_id: UUID,
        status_filter: Optional[ReviewStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ReviewList:
        """Получение списка отзывов о пользователе."""
        offset = (page - 1) * page_size
        reviews, total = await self.repository.list_by_target(
            target_id=user_id,
            status=status_filter,
            limit=page_size,
            offset=offset,
        )
        
        pages = (total + page_size - 1) // page_size
        
        return ReviewList(
            items=reviews,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def update_review_status(
        self,
        review_id: UUID,
        new_status: ReviewStatus,
        admin_id: Optional[UUID] = None,
    ) -> Review:
        """Обновление статуса отзыва (например, модерация)."""
        # Проверяем, что отзыв существует
        review = await self.repository.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundError("Отзыв не найден")

        # Обновляем статус
        updated_review = await self.repository.update_status(review_id, new_status)
        if not updated_review:
            raise ReviewNotFoundError("Отзыв не найден")

        return updated_review

    async def delete_review(
        self,
        review_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Удаление отзыва (автор может удалить только свой отзыв)."""
        review = await self.repository.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundError("Отзыв не найден")

        # Проверяем права: только автор может удалить свой отзыв
        if review.author_id != user_id:
            raise ForbiddenError("Вы можете удалить только свой отзыв")

        return await self.repository.delete(review_id)

    async def check_user_can_review(
        self,
        user_id: UUID,
        trip_id: UUID,
    ) -> tuple[bool, str]:
        """Проверка, может ли пользователь оставить отзыв на поездку."""
        # Получаем поездку
        trip = await self._get_trip(trip_id)
        if not trip:
            return False, "Поездка не найдена"

        # Проверяем статус поездки
        if trip.status != TripStatus.COMPLETED:
            return False, "Отзыв можно оставить только после завершения поездки"

        # Проверяем, что пользователь участник
        participants = await self._get_confirmed_participants(trip_id)
        if user_id not in participants:
            return False, "Вы не являетесь участником этой поездки"

        # Проверяем, что отзыв ещё не существует
        existing = await self.repository.get_by_trip_and_author(trip_id, user_id)
        if existing:
            return False, "Вы уже оставили отзыв на эту поездку"

        return True, ""
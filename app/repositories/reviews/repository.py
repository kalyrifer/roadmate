"""
Repository слой для работы с отзывами (Review).
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reviews.model import Review, ReviewStatus


class ReviewRepository:
    """Repository для работы с отзывами."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        trip_id: UUID,
        author_id: UUID,
        target_id: UUID,
        rating: int,
        text: Optional[str] = None,
    ) -> Review:
        """Создание нового отзыва."""
        review = Review(
            trip_id=trip_id,
            author_id=author_id,
            target_id=target_id,
            rating=rating,
            text=text,
            status=ReviewStatus.PENDING,
        )
        self.session.add(review)
        await self.session.flush()
        await self.session.refresh(review)
        return review

    async def get_by_id(self, review_id: UUID) -> Optional[Review]:
        """Получение отзыва по ID."""
        result = await self.session.execute(
            select(Review)
            .where(Review.id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_by_trip_and_author(self, trip_id: UUID, author_id: UUID) -> Optional[Review]:
        """Получение отзыва по поездке и автору."""
        result = await self.session.execute(
            select(Review)
            .where(
                and_(
                    Review.trip_id == trip_id,
                    Review.author_id == author_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def exists_by_trip_and_author(self, trip_id: UUID, author_id: UUID) -> bool:
        """Проверка существования отзыва от автора на поездку."""
        result = await self.session.execute(
            select(Review.id)
            .where(
                and_(
                    Review.trip_id == trip_id,
                    Review.author_id == author_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_by_trip(
        self,
        trip_id: UUID,
        status: Optional[ReviewStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Review], int]:
        """Получение списка отзывов для поездки."""
        conditions = [Review.trip_id == trip_id]
        if status:
            conditions.append(Review.status == status)

        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(Review.id))
            .where(and_(*conditions))
        )
        total = count_result.scalar()

        # Получаем отзывы
        result = await self.session.execute(
            select(Review)
            .where(and_(*conditions))
            .order_by(Review.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        reviews = list(result.scalars().all())

        return reviews, total

    async def list_by_target(
        self,
        target_id: UUID,
        status: Optional[ReviewStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Review], int]:
        """Получение списка отзывов о пользователе."""
        conditions = [Review.target_id == target_id]
        if status:
            conditions.append(Review.status == status)

        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(Review.id))
            .where(and_(*conditions))
        )
        total = count_result.scalar()

        # Получаем отзывы
        result = await self.session.execute(
            select(Review)
            .where(and_(*conditions))
            .order_by(Review.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        reviews = list(result.scalars().all())

        return reviews, total

    async def list_by_author(
        self,
        author_id: UUID,
        status: Optional[ReviewStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Review], int]:
        """Получение списка отзывов, оставленных пользователем."""
        conditions = [Review.author_id == author_id]
        if status:
            conditions.append(Review.status == status)

        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(Review.id))
            .where(and_(*conditions))
        )
        total = count_result.scalar()

        # Получаем отзывы
        result = await self.session.execute(
            select(Review)
            .where(and_(*conditions))
            .order_by(Review.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        reviews = list(result.scalars().all())

        return reviews, total

    async def update_status(self, review_id: UUID, status: ReviewStatus) -> Optional[Review]:
        """Обновление статуса отзыва."""
        review = await self.get_by_id(review_id)
        if not review:
            return None

        review.status = status
        await self.session.flush()
        await self.session.refresh(review)
        return review

    async def delete(self, review_id: UUID) -> bool:
        """Удаление отзыва."""
        review = await self.get_by_id(review_id)
        if not review:
            return False

        await self.session.delete(review)
        await self.session.flush()
        return True
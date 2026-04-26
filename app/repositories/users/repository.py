"""
Репозиторий для работы с пользователями.

Содержит асинхронные методы для:
- Получения пользователя по email
- Получения пользователя по ID
- Получения пользователя с отзывами
- Создания пользователя
- Обновления пользователя
- Получения количества поездок
"""
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.users.model import User, UserRole
from app.models.reviews.model import Review, ReviewStatus
from app.models.trips.model import Trip, TripStatus


class UserRepository:
    """
    Репозиторий для работы с пользователями.
    
    Обеспечивает доступ к данным пользователей в БД.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория.
        
        Args:
            session: Асинхронная сессия БД
        """
        self.session = session
    
    async def get_user_by_email(self, email: str) -> User | None:
        """
        Получение пользователя по email.
        
        Args:
            email: Email пользователя
            
        Returns:
            User | None: Найденный пользователь или None
        """
        stmt = select(User).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Получение пользователя по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            User | None: Найденный пользователь или None
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_with_reviews(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
    ) -> tuple[User | None, list[Review], int]:
        """
        Получение пользователя с отзывами.
        
        Args:
            user_id: ID пользователя
            limit: Количество отзывов для загрузки
            
        Returns:
            tuple[User | None, list[Review], int]: Кортеж (пользователь, отзывы, количество поездок)
        """
        # Получаем пользователя
        user = await self.get_user_by_id(user_id)
        if not user:
            return None, [], 0
        
        # Получаем опубликованные отзывы о пользователе с автором
        stmt = (
            select(Review)
            .options(selectinload(Review.author))
            .where(Review.target_id == user_id)
            .where(Review.status == ReviewStatus.PUBLISHED.value)
            .order_by(Review.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        reviews = list(result.scalars().all())
        
        # Получаем количество поездок пользователя как водитель
        trips_stmt = (
            select(func.count(Trip.id))
            .where(Trip.driver_id == user_id)
            .where(Trip.status == TripStatus.COMPLETED)
        )
        trips_result = await self.session.execute(trips_stmt)
        trips_count = trips_result.scalar() or 0
        
        return user, reviews, trips_count
    
    async def update_user(
        self,
        user: User,
        update_data: dict[str, Any],
    ) -> User:
        """
        Обновление данных пользователя.
        
        Обновляет только переданные поля.
        
        Args:
            user: Пользователь для обновления
            update_data: Словарь с данными для обновления
            
        Returns:
            User: Обновленный пользователь
        """
        # Обработка имени (может быть "first_name last_name")
        if "name" in update_data and update_data["name"]:
            name_parts = update_data["name"].split(" ", 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Обновление остальных полей
        if "phone" in update_data:
            user.phone = update_data["phone"]
        if "bio" in update_data:
            user.bio = update_data["bio"]
        if "language" in update_data:
            user.language = update_data["language"]
        if "avatar_url" in update_data:
            user.avatar_url = update_data["avatar_url"]
        
        await self.session.flush()
        await self.session.refresh(user)
        return user
    
    async def create_user(self, user_data: dict[str, Any]) -> User:
        """
        Создание нового пользователя.
        
        Args:
            user_data: Словарь с данными пользователя
            
        Returns:
            User: Созданный пользователь
        """
        user = User(
            email=user_data["email"],
            password_hash=user_data["password_hash"],
            first_name=user_data["first_name"],
            last_name=user_data.get("last_name", ""),
            role=user_data.get("role", UserRole.user),
            is_active=user_data.get("is_active", True),
            is_blocked=user_data.get("is_blocked", False),
            rating_average=user_data.get("rating_average", 0.0),
            rating_count=user_data.get("rating_count", 0),
            language=user_data.get("language", "ru"),
            timezone=user_data.get("timezone", "Europe/Moscow"),
        )
        
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
    
    async def commit(self) -> None:
        """Коммит транзакции."""
        await self.session.commit()
    
    async def rollback(self) -> None:
        """Откат транзакции."""
        await self.session.rollback()
"""
Сервис для работы с пользователями.

Содержит бизнес-логику для:
- Получения профиля пользователя
- Обновления профиля пользователя
- Загрузки аватара
"""
import logging
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.users.model import User, UserRole
from app.repositories.users.repository import UserRepository
from app.schemas.users.schemas import (
    ReviewAuthorInProfile,
    ReviewInProfileResponse,
    UserResponse,
    UserUpdateRequest,
)

# Настройка логирования
logger = logging.getLogger(__name__)

# Разрешённые типы файлов для аватара
ALLOWED_AVATAR_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
# Максимальный размер файла (10 MB)
MAX_AVATAR_SIZE = 10 * 1024 * 1024


class UserService:
    """
    Сервис для работы с пользователями.
    
    Обеспечивает бизнес-логику для работы с профилями.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация сервиса.
        
        Args:
            session: Асинхронная сессия БД
        """
        self.session = session
        self.repository = UserRepository(session)
    
    async def get_user_profile(
        self,
        user_id: uuid.UUID,
    ) -> UserResponse:
        """
        Получение профиля пользователя.
        
        Включает отзывы и количество поездок.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            UserResponse: Данные профиля пользователя
            
        Raises:
            HTTPException: 404 если пользователь не найден
        """
        user, reviews, trips_count = await self.repository.get_user_with_reviews(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Преобразуем отзывы в схему
        def _build_author(author: User | None) -> ReviewAuthorInProfile | None:
            if author is None:
                return None
            first = (author.first_name or "").strip()
            last = (author.last_name or "").strip()
            full_name = f"{first} {last}".strip()
            if not full_name:
                full_name = author.email.split("@")[0] if author.email else "Участник"
            return ReviewAuthorInProfile(
                id=str(author.id),
                name=full_name,
                avatar_url=author.avatar_url,
            )

        reviews_schema = [
            ReviewInProfileResponse(
                id=str(r.id),
                author_id=str(r.author_id),
                author=_build_author(r.author),
                rating=r.rating,
                text=r.text,
                created_at=r.created_at,
            )
            for r in reviews
        ]
        
        return UserResponse.from_orm_with_reviews(
            user=user,
            reviews=reviews_schema,
            trips_count=trips_count,
        )
    
    async def update_user_profile(
        self,
        current_user: User,
        target_user_id: uuid.UUID,
        update_data: UserUpdateRequest,
        avatar_file: UploadFile | None = None,
    ) -> UserResponse:
        """
        Обновление профиля пользователя.
        
        Проверяет права доступа (владелец или админ).
        Поддерживает загрузку аватара.
        
        Args:
            current_user: Текущий авторизованный пользователь
            target_user_id: ID пользователя для обновления
            update_data: Данные для обновления
            avatar_file: Файл аватара
            
        Returns:
            UserResponse: Обновленный профиль
            
        Raises:
            HTTPException: 403 если нет прав
            HTTPException: 404 если пользователь не найден
            HTTPException: 400 если неверный тип файла
        """
        # Проверка прав доступа
        is_owner = current_user.id == target_user_id
        is_admin = current_user.role == UserRole.admin
        
        if not is_owner and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to edit this profile",
            )
        
        # Получаем пользователя
        user = await self.repository.get_user_by_id(target_user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Обработка файла аватара
        avatar_url: str | None = None
        if avatar_file:
            avatar_url = await self._save_avatar(avatar_file, user.id)
        
        # Подготовка данных для обновления
        update_dict: dict[str, Any] = {}
        
        if update_data.name is not None:
            update_dict["name"] = update_data.name
        if update_data.phone is not None:
            update_dict["phone"] = update_data.phone
        if update_data.bio is not None:
            update_dict["bio"] = update_data.bio
        if update_data.language is not None:
            update_dict["language"] = update_data.language
        if avatar_url is not None:
            update_dict["avatar_url"] = avatar_url
        
        # Обновление пользователя
        if update_dict:
            user = await self.repository.update_user(user, update_dict)
            await self.repository.commit()
        
        # Логирование изменений
        logger.info(
            f"User {current_user.id} updated profile for user {target_user_id}"
        )
        
        # Возвращаем обновленный профиль
        return await self.get_user_profile(target_user_id)
    
    async def _save_avatar(
        self,
        avatar_file: UploadFile,
        user_id: uuid.UUID,
    ) -> str:
        """
        Сохранение аватара пользователя.
        
        Проверяет тип и размер файла,
        сохраняет в локальную папку.
        
        Args:
            avatar_file: Файл аватара
            user_id: ID пользователя
            
        Returns:
            str: URL сохраненного аватара
            
        Raises:
            HTTPException: 400 если неверный тип или размер файла
        """
        # Проверка типа файла
        content_type = avatar_file.content_type
        if content_type not in ALLOWED_AVATAR_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type",
            )
        
        # Проверка размера файла
        avatar_file.file.seek(0, 2)  # Переход в конец файла
        file_size = avatar_file.tell()
        avatar_file.file.seek(0)  # Возврат в начало
        
        if file_size > MAX_AVATAR_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large",
            )
        
        # Определение расширения файла
        ext = ".jpg"
        if content_type == "image/png":
            ext = ".png"
        elif content_type == "image/gif":
            ext = ".gif"
        elif content_type == "image/webp":
            ext = ".webp"
        
        # Создание директории для аватаров
        upload_dir = Path(settings.files.UPLOAD_DIR) / "avatars"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерация уникального имени файла
        filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = upload_dir / filename
        
        # Сохранение файла
        content = await avatar_file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Формирование URL
        avatar_url = f"/uploads/avatars/{filename}"
        
        logger.info(f"Avatar saved: {avatar_url}")
        
        return avatar_url
    
    def check_can_view_profile(
        self,
        current_user: User,
        target_user_id: uuid.UUID,
    ) -> bool:
        """
        Проверка права на просмотр профиля.
        
        Args:
            current_user: Текущий пользователь
            target_user_id: ID целевого пользователя
            
        Returns:
            bool: True если можно смотреть
        """
        # Владелец может смотреть свой профиль
        if current_user.id == target_user_id:
            return True
        
        # Админ может смотреть любой профиль
        if current_user.role == UserRole.admin:
            return True
        
        # Блокированные пользователи не могут смотреть профили
        if current_user.is_blocked or not current_user.is_active:
            return False
        
        return True
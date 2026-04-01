"""
Роутер домена Users.

Эндпоинты:
- GET /{user_id} — просмотр профиля пользователя
- PUT /{user_id} — редактирование профиля пользователя
"""
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.models.users.model import User, UserRole
from app.schemas.users.schemas import UserResponse, UserUpdateRequest
from app.services.users.service import UserService

router = APIRouter()


async def get_user_service(db: AsyncSession) -> UserService:
    """
    Получение сервиса пользователей.
    
    Args:
        db: Сессия БД
        
    Returns:
        UserService: Экземпляр сервиса
    """
    return UserService(db)


# Типы для зависимостей
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Просмотр профиля пользователя.
    
    Права доступа:
    - Пользователь может смотреть свой профиль
    - Админ может смотреть любой профиль
    
    Args:
        user_id: ID пользователя (UUID строка)
        current_user: Текущий авторизованный пользователь
        user_service: Сервис пользователей
        
    Returns:
        UserResponse: Данные профиля пользователя
        
    Raises:
        HTTPException: 403 если нет прав
        HTTPException: 404 если пользователь не найден
    """
    # Валидация UUID
    try:
        target_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    # Проверка прав доступа
    if not user_service.check_can_view_profile(current_user, target_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this profile",
        )
    
    return await user_service.get_user_profile(target_uuid)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_profile(
    user_id: str,
    name: str | None = Form(None, description="Имя пользователя"),
    phone: str | None = Form(None, description="Номер телефона"),
    bio: str | None = Form(None, description="Описание профиля"),
    language: str | None = Form(None, description="Язык интерфейса (ru, en)"),
    avatar: UploadFile | None = Form(None, description="Файл аватара"),
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Редактирование профиля пользователя.
    
    Поддерживает обновление имени, телефона, bio, языка интерфейса
    и загрузку аватара через file upload.
    
    Права доступа:
    - Пользователь может редактировать только свой профиль
    - Админ может редактировать любой профиль
    
    Args:
        user_id: ID пользователя (UUID строка)
        name: Имя пользователя
        phone: Номер телефона
        bio: Описание профиля
        language: Язык интерфейса
        avatar: Файл аватара
        current_user: Текущий авторизованный пользователь
        user_service: Сервис пользователей
        
    Returns:
        UserResponse: Обновленный профиль пользователя
        
    Raises:
        HTTPException: 400 если неверный формат данных
        HTTPException: 403 если нет прав
        HTTPException: 404 если пользователь не найден
    """
    # Валидация UUID
    try:
        target_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    # Создание объекта обновления
    update_data = UserUpdateRequest(
        name=name,
        phone=phone,
        bio=bio,
        language=language,
    )
    
    return await user_service.update_user_profile(
        current_user=current_user,
        target_user_id=target_uuid,
        update_data=update_data,
        avatar_file=avatar,
    )


# Дополнительные эндпоинты для удобства

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Просмотр своего профиля.
    
    Shorthand для GET /{user_id} где user_id = текущий пользователь.
    
    Args:
        current_user: Текущий авторизованный пользователь
        user_service: Сервис пользователей
        
    Returns:
        UserResponse: Данные профиля пользователя
    """
    return await user_service.get_user_profile(current_user.id)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    name: str | None = Form(None, description="Имя пользователя"),
    phone: str | None = Form(None, description="Номер телефона"),
    bio: str | None = Form(None, description="Описание профиля"),
    language: str | None = Form(None, description="Язык интерфейса (ru, en)"),
    avatar: UploadFile | None = Form(None, description="Файл аватара"),
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserServiceDep,
) -> UserResponse:
    """
    Редактирование своего профиля.
    
    Shorthand для PUT /{user_id} где user_id = текущий пользователь.
    
    Args:
        name: Имя пользователя
        phone: Номер телефона
        bio: Описание профиля
        language: Язык интерфейса
        avatar: Файл аватара
        current_user: Текущий авторизованный пользователь
        user_service: Сервис пользователей
        
    Returns:
        UserResponse: Обновленный профиль пользователя
    """
    update_data = UserUpdateRequest(
        name=name,
        phone=phone,
        bio=bio,
        language=language,
    )
    
    return await user_service.update_user_profile(
        current_user=current_user,
        target_user_id=current_user.id,
        update_data=update_data,
        avatar_file=avatar,
    )
"""
Dependencies для FastAPI.

Содержит зависимости для:
- Получения текущего пользователя
- Получения администратора
- Проверки аутентификации
"""
from __future__ import annotations

import logging
import uuid
from typing import Annotated, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import decode_access_token
from app.models.users.model import User, UserRole
from app.repositories.users.repository import UserRepository

# Настройка логирования
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency для получения текущего авторизованного пользователя.
    
    Извлекает JWT токен из заголовка Authorization,
    декодирует его и возвращает объект User из БД.
    
    Args:
        credentials: Учетные данные из заголовка Authorization
        db: Сессия БД
        
    Returns:
        User: Объект пользователя
        
    Raises:
        HTTPException: 401 если токен недействителен
    """
    # Проверка наличия токена
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Декодирование токена
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Получение user_id из payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Поиск пользователя в БД
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    repository = UserRepository(db)
    user = await repository.get_user_by_id(user_uuid)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверка статуса пользователя
    if not user.is_active or user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency для получения администратора.
    
    Расширяет get_current_user, дополнительно проверяя
    роль пользователя.
    
    Args:
        current_user: Текущий пользователь из get_current_user
        
    Returns:
        User: Объект администратора
        
    Raises:
        HTTPException: 403 если недостаточно прав
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    return current_user


# Типы для удобства использования в роутерах
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]


async def get_current_user_optional(
    credentials: Annotated[Union[HTTPAuthorizationCredentials, None], Depends(security)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> Optional[User]:
    """
    Dependency для получения текущего пользователя (опционально).
    
    Если токен не предоставлен или недействителен, возвращает None.
    """
    if not credentials or not db:
        print("[DEBUG get_current_user_optional] No credentials or db")
        return None
    
    token = credentials.credentials
    print(f"[DEBUG get_current_user_optional] Token received: {token[:50] if token else 'None'}...")
    
    payload = decode_access_token(token)
    if not payload:
        print("[DEBUG get_current_user_optional] Invalid token payload")
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        print("[DEBUG get_current_user_optional] No user_id in payload")
        return None
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        print("[DEBUG get_current_user_optional] Invalid UUID in user_id")
        return None
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)
    print(f"[DEBUG get_current_user_optional] User found: {user.id if user else 'None'}")
    return user


CurrentUserOptional = Annotated[User, Depends(get_current_user_optional)]
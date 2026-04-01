"""
Роутер домена Auth.
Эндпоинты:
- POST /register — регистрация
- POST /login — вход
- POST /logout — выход
- GET /me — текущий пользователь
- POST /refresh — обновление токена
- POST /password-reset — сброс пароля
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import get_current_user
from app.models.users.model import User
from app.schemas.auth import (
    ErrorDetail,
    LoginRequest,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth.service import AuthService
from app.repositories.users.repository import UserRepository

# Security scheme for JWT
security = HTTPBearer(auto_error=False)

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    responses={
        400: {"model": ErrorDetail, "description": "Email уже зарегистрирован"},
        422: {"model": ErrorDetail, "description": "Невалидные данные"},
    },
    summary="Регистрация нового пользователя",
    description="Регистрирует нового пользователя с email и паролем. Возвращает JWT токен.",
)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Регистрация нового пользователя.
    
    Принимает email, пароль и имя. Проверяет уникальность email,
    хэширует пароль и создаёт пользователя.
    
    Возвращает JWT токен доступа.
    """
    user_repository = UserRepository(db)
    auth_service = AuthService(user_repository)
    
    try:
        result = await auth_service.register_user(data)
        return result
    except ValueError as e:
        if str(e) == "Email already registered":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorDetail, "description": "Неверный email или пароль"},
        422: {"model": ErrorDetail, "description": "Невалидные данные"},
    },
    summary="Вход в систему",
    description="Аутентификация пользователя по email и паролю. Возвращает JWT токен.",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Вход пользователя в систему.
    
    Принимает email и пароль. Проверяет учетные данные
    и возвращает JWT токен доступа.
    """
    user_repository = UserRepository(db)
    auth_service = AuthService(user_repository)
    
    try:
        result = await auth_service.login_user(data.email, data.password)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )


@router.post(
    "/logout",
    response_model=dict,
    responses={
        401: {"model": ErrorDetail, "description": "Неавторизован"},
    },
    summary="Выход из системы",
    description="Выполняет выход пользователя из системы.",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """
    Выход пользователя из системы.
    
    Защищенный endpoint. Требует валидный JWT токен.
    Логирует событие выхода.
    """
    from app.services.auth.service import AuthService
    from app.repositories.users.repository import UserRepository
    
    # Используем репозиторий для доступа к сервису
    # В данном случае просто возвращаем результат
    logger = logging.getLogger(__name__)
    logger.info(f"User {current_user.email} logged out")
    
    return {"message": "Successfully logged out"}


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorDetail, "description": "Недействительный токен"},
    },
    summary="Получение текущего пользователя",
    description="Возвращает данные авторизованного пользователя.",
)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Получение текущего пользователя.
    
    Извлекает JWT токен из заголовка Authorization,
    декодирует его и возвращает данные пользователя.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user_repository = UserRepository(db)
    auth_service = AuthService(user_repository)
    
    try:
        result = await auth_service.get_current_user(credentials.credentials)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


@router.post("/refresh")
async def refresh_token() -> dict[str, str]:
    """Обновление access токена."""
    return {"message": "Refresh token endpoint"}


@router.post("/password-reset")
async def reset_password() -> dict[str, str]:
    """Запрос на сброс пароля."""
    return {"message": "Password reset endpoint"}
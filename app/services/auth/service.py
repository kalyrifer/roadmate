"""
Сервис аутентификации и авторизации.

Содержит бизнес-логику для:
- Регистрации пользователей
- Входа в систему
- Проверки токенов
- Получения текущего пользователя
- Выхода из системы
"""




import logging
import uuid
from datetime import timedelta
from typing import Any

logger = logging.getLogger(__name__)

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.users.model import User
from app.repositories.users.repository import UserRepository
from app.schemas.auth import TokenResponse, UserRegisterRequest, UserResponse


class AuthService:
    """
    Сервис для работы с аутентификацией и авторизацией.
    
    Обеспечивает бизнес-логику для регистрации и входа.
    """
    
    def __init__(self, user_repository: UserRepository) -> None:
        """
        Инициализация сервиса.
        
        Args:
            user_repository: Репозиторий пользователей
        """
        self.user_repository = user_repository
    
    async def register_user(
        self,
        data: UserRegisterRequest,
    ) -> TokenResponse:
        """
        Регистрация нового пользователя.
        
        Валидирует данные, проверяет уникальность email,
        хэширует пароль и создаёт пользователя.
        
        Args:
            data: Данные для регистрации
            
        Returns:
            TokenResponse: Токен и данные пользователя
            
        Raises:
            ValueError: Если email уже зарегистрирован
        """
        # Нормализация email (нижний регистр) - уже делается в схеме
        email = data.email.lower().strip()
        
        # Проверка уникальности email
        existing_user = await self.user_repository.get_user_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Хэширование пароля
        password_hash = get_password_hash(data.password)
        
        # Создание пользователя
        user_data: dict[str, Any] = {
            "email": email,
            "password_hash": password_hash,
            "first_name": data.name.strip(),  # Используем name как first_name
            "last_name": "",
            "role": "user",  # Default role
            "is_active": True,
            "is_blocked": False,
            "rating_average": 0.0,
            "rating_count": 0,
            "language": "ru",
            "timezone": "Europe/Moscow",
        }
        
        user = await self.user_repository.create_user(user_data)
        await self.user_repository.commit()
        
        # Создание JWT токена
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=30),
        )
        
        # Формирование ответа
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.first_name,
                rating_average=float(user.rating_average) if user.rating_average else 0.0,
                rating_count=user.rating_count or 0,
            ),
        )
    
    async def login_user(
        self,
        email: str,
        password: str,
    ) -> TokenResponse:
        """
        Вход пользователя в систему.
        
        Валидирует email и пароль, генерирует JWT токен.
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            
        Returns:
            TokenResponse: Токен и данные пользователя
            
        Raises:
            ValueError: Если email или пароль неверны
        """
        # Нормализация email
        email = email.lower().strip()
        
        # Поиск пользователя
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            raise ValueError("Incorrect email or password")
        
        # Проверка пароля
        if not verify_password(password, user.password_hash):
            raise ValueError("Incorrect email or password")
        
        # Проверка статуса
        if not user.is_active or user.is_blocked:
            raise ValueError("Incorrect email or password")
        
        # Создание JWT токена
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=30),
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.first_name,
                rating_average=float(user.rating_average) if user.rating_average else 0.0,
                rating_count=user.rating_count or 0,
            ),
        )
    
    async def get_current_user(
        self,
        token: str,
    ) -> UserResponse:
        """
        Получение текущего пользователя по JWT токену.
        
        Декодирует токен, проверяет подпись и срок действия,
        находит пользователя в БД.
        
        Args:
            token: JWT токен
            
        Returns:
            UserResponse: Данные пользователя
            
        Raises:
            ValueError: Если токен недействителен или пользователь не найден
        """
        # Декодирование токена
        payload = decode_access_token(token)
        if not payload:
            raise ValueError("Could not validate credentials")
        
        # Получение данных из payload
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Could not validate credentials")
        
        # Поиск пользователя
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise ValueError("Could not validate credentials")
        
        user = await self.user_repository.get_user_by_id(user_uuid)
        if not user:
            raise ValueError("Could not validate credentials")
        
        # Проверка статуса
        if not user.is_active or user.is_blocked:
            raise ValueError("Could not validate credentials")
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.first_name,
            rating_average=float(user.rating_average) if user.rating_average else 0.0,
            rating_count=user.rating_count or 0,
        )
    
    async def logout_user(
        self,
        user: User,
    ) -> dict[str, str]:
        """
        Выход пользователя из системы.
        
        Логирует событие выхода пользователя.
        Placeholder для будущей реализации blacklist токенов.
        
        Args:
            user: Пользователь, выполняющий выход
            
        Returns:
            dict[str, str]: Сообщение об успешном выходе
        """
        logger.info(f"User {user.email} logged out")
        
        # Placeholder для future: добавление токена в blacklist
        # При использовании refresh token
        
        return {"message": "Successfully logged out"}
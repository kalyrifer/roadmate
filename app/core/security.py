"""
Безопасность: JWT токены и пароли.
"""
import hashlib
import types
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
import bcrypt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = types.SimpleNamespace(__version__=getattr(bcrypt, "__version__", "unknown"))

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Данные токена."""
    # В токене `sub` хранится как UUID строкой (см. AuthService).
    user_id: str | None = None
    exp: datetime | None = None


class Token(BaseModel):
    """Структура токена."""
    access_token: str
    token_type: str = "bearer"


def hash_password(password: str) -> str:
    """
    Возвращает безопасный хэш пароля.
    
    Использует bcrypt через Passlib для безопасного хэширования.
    Каждый вызов генерирует уникальную соль (salt).
    
    Args:
        password: Пароль в открытом виде
        
    Returns:
        str: Хэш пароля для хранения в БД
    """
    normalized_password = password.encode("utf-8")
    if len(normalized_password) > 72:
        normalized_password = hashlib.sha256(normalized_password).hexdigest().encode("utf-8")
    return pwd_context.hash(normalized_password.decode("utf-8"))


# Alias for backward compatibility
get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Сравнивает пароль с хэшем.
    
    Защищен от timing attacks через Passlib.
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хэш пароля из базы
        
    Returns:
        bool: True если пароли совпадают, False иначе
    """
    normalized_password = plain_password.encode("utf-8")
    if len(normalized_password) > 72:
        normalized_password = hashlib.sha256(normalized_password).hexdigest().encode("utf-8")
    return pwd_context.verify(normalized_password.decode("utf-8"), hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Создание JWT токена."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=__import__('datetime').timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz=__import__('datetime').timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    # Получаем_secret_key как строку
    secret_key = settings.secret_key.get_secret_value()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> TokenData | None:
    """Декодирование JWT токена."""
    try:
        secret_key = settings.secret_key.get_secret_value()
        payload = jwt.decode(token, secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")  # JWT: sub = str(uuid)
        if user_id is None:
            return None
        return TokenData(user_id=user_id)
    except JWTError:
        return None


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Декодирование JWT токена с возвратом payload.
    
    Args:
        token: JWT токен
        
    Returns:
        dict[str, Any] | None: Payload токена или None при ошибке
    """
    try:
        secret_key = settings.secret_key.get_secret_value()
        payload = jwt.decode(token, secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None

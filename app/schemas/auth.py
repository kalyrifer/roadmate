"""
Схемы для аутентификации и авторизации.

Содержит Pydantic схемы для:
- Регистрации пользователя
- Входа в систему
- Ответов с токенами
"""
import re
from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

PASSWORD_MIN_LENGTH = 8

# Чёрный список самых распространённых слабых паролей.
# Сравнение регистронезависимое.
WEAK_PASSWORDS: frozenset[str] = frozenset(
    {
        "12345678",
        "123456789",
        "1234567890",
        "qwerty",
        "qwerty123",
        "qwertyuiop",
        "password",
        "password1",
        "password123",
        "passw0rd",
        "111111",
        "11111111",
        "000000",
        "00000000",
        "abc12345",
        "abcd1234",
        "iloveyou",
        "admin",
        "admin123",
        "letmein",
        "welcome",
        "welcome1",
        "monkey",
        "dragon",
        "football",
        "baseball",
        "starwars",
        "qazwsx",
        "qazwsx123",
        "trustno1",
        "master",
        "freedom",
        "sunshine",
        "shadow",
        "superman",
        "ninja",
        "mustang",
        # Популярные «русские» пароли
        "пароль",
        "пароль123",
        "йцукен",
        "йцукен123",
    }
)


def validate_password_strength(password: str) -> str:
    """Базовая валидация пароля.

    Требования:
    - не короче PASSWORD_MIN_LENGTH символов;
    - содержит хотя бы одну букву и хотя бы одну цифру;
    - не входит в список самых распространённых слабых паролей и не состоит
      только из одной повторяющейся цифры/буквы.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
        )

    has_letter = bool(re.search(r"[A-Za-zА-Яа-яЁё]", password))
    has_digit = bool(re.search(r"\d", password))
    if not (has_letter and has_digit):
        raise ValueError("Password must contain both letters and digits")

    if password.lower() in WEAK_PASSWORDS:
        raise ValueError("Password is too common, please choose a stronger one")

    if len(set(password)) == 1:
        raise ValueError("Password must not consist of a single repeated character")

    return password


class UserRegisterRequest(BaseModel):
    """
    Схема для регистрации нового пользователя.
    
    Валидирует email, пароль и имя.
    """
    email: str = Field(
        ...,
        description="Email пользователя",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        description=(
            f"Пароль пользователя (минимум {PASSWORD_MIN_LENGTH} символов, "
            "должен содержать буквы и цифры; распространённые пароли запрещены)"
        ),
        min_length=PASSWORD_MIN_LENGTH,
        examples=["securePassword123"],
    )
    name: str = Field(
        ...,
        description="Имя пользователя",
        min_length=1,
        max_length=100,
        examples=["Иван"],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Проверяем минимальную сложность пароля."""
        return validate_password_strength(v)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """
        Валидация и нормализация email.
        
        - Приводит к нижнему регистру
        - Убирает лишние пробелы
        
        Args:
            v: Email для валидации
            
        Returns:
            Нормализованный email
            
        Raises:
            ValueError: Если email некорректен
        """
        # Убираем пробелы
        v = v.strip()
        # Проверяем базовый формат email
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Валидация имени.
        
        - Убирает лишние пробелы
        
        Args:
            v: Имя для валидации
            
        Returns:
            Нормализованное имя
        """
        return v.strip()

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "title": "UserRegisterRequest",
            "description": "Схема запроса на регистрацию пользователя",
        },
    )


class UserResponse(BaseModel):
    """
    Схема ответа с данными пользователя.
    
    Не включает чувствительные данные (пароль, хэш).
    """
    id: str = Field(..., description="Уникальный идентификатор пользователя")
    email: str = Field(..., description="Email пользователя")
    name: str = Field(..., description="Имя пользователя")
    rating_average: float = Field(
        default=0.0,
        description="Средний рейтинг пользователя",
    )
    rating_count: int = Field(
        default=0,
        description="Количество отзывов",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "title": "UserResponse",
            "description": "Схема ответа с данными пользователя",
        },
    )


class TokenResponse(BaseModel):
    """
    Схема ответа с токеном доступа.
    
    Возвращается после успешной регистрации или входа.
    """
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field(
        default="bearer",
        description="Тип токена",
    )
    user: UserResponse = Field(..., description="Данные пользователя")

    model_config = ConfigDict(
        json_schema_extra={
            "title": "TokenResponse",
            "description": "Схема ответа с токеном доступа",
        },
    )


class LoginRequest(BaseModel):
    """
    Схема для входа в систему.
    """
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., description="Пароль пользователя")

    model_config = ConfigDict(
        json_schema_extra={
            "title": "LoginRequest",
            "description": "Схема запроса на вход в систему",
        },
    )


class ErrorDetail(BaseModel):
    """
    Схема для ошибок.
    """
    detail: str = Field(..., description="Сообщение об ошибке")

    model_config = ConfigDict(
        json_schema_extra={
            "title": "ErrorDetail",
            "description": "Схема для ошибок API",
        },
    )
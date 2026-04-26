"""
Схемы для работы с пользователями.

Содержит Pydantic схемы для:
- Ответа с данными пользователя
- Обновления профиля пользователя
- Отзыва о пользователе
"""
from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class ReviewAuthorInProfile(BaseModel):
    """Краткая информация об авторе отзыва."""

    id: str = Field(..., description="ID автора отзыва")
    name: str = Field(..., description="Имя автора отзыва")
    avatar_url: str | None = Field(None, description="URL аватара автора")

    model_config = ConfigDict(from_attributes=True)


class ReviewInProfileResponse(BaseModel):
    """
    Схема отзыва в профиле пользователя.
    
    Используется для отображения отзывов в профиле пользователя.
    """
    id: str = Field(..., description="Уникальный идентификатор отзыва")
    author_id: str = Field(..., description="ID автора отзыва")
    author: ReviewAuthorInProfile | None = Field(
        None, description="Краткая информация об авторе отзыва"
    )
    rating: int = Field(..., description="Оценка от 1 до 5", ge=1, le=5)
    text: str | None = Field(None, description="Текст отзыва")
    created_at: datetime = Field(..., description="Время создания отзыва")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "title": "ReviewInProfileResponse",
            "description": "Схема отзыва в профиле пользователя",
        },
    )


class UserResponse(BaseModel):
    """
    Схема ответа с данными пользователя.
    
    Используется для возврата данных профиля пользователя.
    Не включает чувствительные данные (пароль, хэш).
    """
    id: str = Field(..., description="Уникальный идентификатор пользователя")
    email: str = Field(..., description="Email пользователя")
    name: str = Field(..., description="Имя пользователя (имя и фамилия)")
    phone: str | None = Field(None, description="Номер телефона")
    avatar_url: str | None = Field(None, description="URL аватара")
    bio: str | None = Field(None, description="Описание профиля")
    rating_average: float = Field(
        default=0.0,
        description="Средний рейтинг пользователя",
        ge=0.0,
        le=5.0,
    )
    rating_count: int = Field(
        default=0,
        description="Количество отзывов",
        ge=0,
    )
    trips_count: int = Field(
        default=0,
        description="Количество поездок",
        ge=0,
    )
    reviews: list[ReviewInProfileResponse] = Field(
        default_factory=list,
        description="Отзывы о пользователе",
    )
    created_at: datetime = Field(..., description="Время создания аккаунта")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "title": "UserResponse",
            "description": "Схема ответа с данными пользователя",
        },
    )

    @classmethod
    def from_orm_with_reviews(
        cls,
        user: Any,
        reviews: list[ReviewInProfileResponse] | None = None,
        trips_count: int = 0,
    ) -> "UserResponse":
        """
        Создание схемы из ORM модели с дополнительными данными.
        
        Объединяет first_name и last_name в одно поле name.
        
        Args:
            user: ORM модель пользователя
            reviews: Список отзывов
            trips_count: Количество поездок
            
        Returns:
            UserResponse: Схема пользователя
        """
        name = f"{user.first_name} {user.last_name}".strip()
        
        return cls(
            id=str(user.id),
            email=user.email,
            name=name or user.email.split("@")[0],
            phone=user.phone,
            avatar_url=user.avatar_url,
            bio=user.bio,
            rating_average=float(user.rating_average) if user.rating_average else 0.0,
            rating_count=user.rating_count,
            trips_count=trips_count,
            reviews=reviews or [],
            created_at=user.created_at,
        )


class UserUpdateRequest(BaseModel):
    """
    Схема для обновления профиля пользователя.
    
    Поддерживает изменение имени, телефона, bio и языка интерфейса.
    Поля role, rating и другие sensitive данные недоступны для изменения.
    """
    name: str | None = Field(
        None,
        description="Имя пользователя",
        min_length=1,
        max_length=200,
    )
    phone: str | None = Field(
        None,
        description="Номер телефона",
        pattern=r"^\+?[0-9]{10,15}$",
    )
    bio: str | None = Field(
        None,
        description="Описание профиля",
        max_length=1000,
    )
    language: str | None = Field(
        None,
        description="Язык интерфейса (ru, en)",
        pattern=r"^(ru|en)$",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """
        Валидация имени.
        
        Убирает лишние пробелы.
        
        Args:
            v: Имя для валидации
            
        Returns:
            str | None: Нормализованное имя или None
        """
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """
        Валидация телефона.
        
        Убирает лишние символы.
        
        Args:
            v: Телефон для валидации
            
        Returns:
            str | None: Нормализованный телефон или None
        """
        if v is not None:
            v = v.strip()
            if not v:
                return None
            # Убираем все пробелы и дефисы
            v = "".join(c for c in v if c.isdigit() or c == "+")
        return v

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: str | None) -> str | None:
        """
        Валидация bio.
        
        Убирает лишние пробелы.
        
        Args:
            v: Bio для валидации
            
        Returns:
            str | None: Нормализованное bio или None
        """
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "title": "UserUpdateRequest",
            "description": "Схема для обновления профиля пользователя",
        },
    )


class UserProfileShortResponse(BaseModel):
    """
    Схема краткого ответа с данными пользователя.
    
    Используется для списков и кратких данных.
    """
    id: str = Field(..., description="Уникальный идентификатор пользователя")
    name: str = Field(..., description="Имя пользователя")
    avatar_url: str | None = Field(None, description="URL аватара")
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
            "title": "UserProfileShortResponse",
            "description": "Схема краткого ответа с данными пользователя",
        },
    )
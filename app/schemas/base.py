"""
Базовые Pydantic схемы с поддержкой локализации.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.config import settings


class BaseSchema(BaseModel):
    """Базовая схема с конфигурацией."""
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseSchema):
    """Миксин для временных меток."""
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LocalizedString(BaseSchema):
    """Локализованная строка (ru/en)."""
    ru: str | None = None
    en: str | None = None


class PaginationParams(BaseModel):
    """Параметры пагинации."""
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseSchema):
    """Ответ с пагинацией."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int


class LanguageParams(BaseModel):
    """Параметр языка в запросе."""
    lang: str = settings.DEFAULT_LANGUAGE

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.lang not in settings.SUPPORTED_LANGUAGES:
            self.lang = settings.DEFAULT_LANGUAGE
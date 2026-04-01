"""
Конфигурация приложения.

Группировка по категориям:
- База данных (Database)
- Безопасность (Security)
- JWT токены
- CORS
- Файлы
- Локализация
- Логирование
"""
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Настройки базы данных."""

    # Основной URL для подключения к БД
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/roadmate2",
        description="URL для подключения к PostgreSQL"
    )

    # URL для синхронного подключения (для миграций Alembic)
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/roadmate2",
        description="Синхронный URL для миграций"
    )

    # Пул соединений
    DATABASE_POOL_SIZE: int = Field(default=20, description="Максимальный размер пула")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Максимальное переполнение пула")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="Таймаут ожидания соединения")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Время жизни соединения (сек)")

    # Настройки отладки SQL запросов
    DATABASE_ECHO: bool = Field(default=False, description="Выводить SQL запросы в лог")

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class SecuritySettings(BaseSettings):
    """Настройки безопасности."""

    # Секретный ключ для подписи токенов
    SECRET_KEY: SecretStr = Field(
        default=SecretStr("CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY"),
        description="Секретный ключ для JWT"
    )

    # Алгоритм хеширования
    ALGORITHM: str = Field(default="HS256", description="Алгоритм подписи JWT")

    # Время жизни токенов
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Время жизни access токена (мин)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Время жизни refresh токена (дней)")

    # Bcrypt настройки
    BCRYPT_ROUNDS: int = Field(default=12, description="Количество раундов bcrypt")

    # OAuth2 настройки
    OAUTH2_PROVIDER: str = Field(default="jwt", description="OAuth2 провайдер")
    OAUTH2_TOKEN_URL: str = Field(default="/api/v1/auth/login", description="URL для получения токена")

    # CORS настройки
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Разрешённые источники для CORS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Разрешить куки и заголовки авторизации")
    CORS_ALLOW_METHODS: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        description="Разрешённые методы"
    )
    CORS_ALLOW_HEADERS: list[str] = Field(
        default=["*"],
        description="Разрешённые заголовки"
    )

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Включить rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Запросов в минуту")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="Запросов в час")

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class JWTSettings(BaseSettings):
    """Настройки JWT токенов (отдельная категория для удобства)."""

    SECRET_KEY: SecretStr = Field(
        default=SecretStr("CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY"),
        description="Секретный ключ для подписи токенов"
    )
    ALGORITHM: str = Field(default="HS256", description="Алгоритм подписи")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Время жизни access токена")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Время жизни refresh токена")

    # Настройки JWT payload
    JWT_SUBJECT: str = Field(default="access", description="Тип токена")
    JWT_AUDIENCE: str | None = Field(default=None, description="Аудитория токена")
    JWT_ISSUER: str | None = Field(default=None, description="Издатель токена")

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class CORSSettings(BaseSettings):
    """Настройки CORS."""

    ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Разрешённые источники"
    )
    ALLOW_CREDENTIALS: bool = Field(default=True, description="Разрешить куки")
    ALLOW_METHODS: list[str] = Field(default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    ALLOW_HEADERS: list[str] = Field(default=["*"])

    model_config = SettingsConfigDict(
        env_prefix="CORS_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class FilesSettings(BaseSettings):
    """Настройки работы с файлами."""

    # Пути для загрузки файлов
    UPLOAD_DIR: str = Field(
        default="./uploads",
        description="Директория для загрузки файлов"
    )
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        description="Максимальный размер файла (байт)"
    )

    # Разрешённые типы файлов
    ALLOWED_IMAGE_TYPES: list[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "image/webp"],
        description="Разрешённые типы изображений"
    )
    ALLOWED_DOCUMENT_TYPES: list[str] = Field(
        default=["application/pdf", "application/msword", 
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        description="Разрешённые типы документов"
    )

    # Настройки S3 (опционально для продакшена)
    S3_ENABLED: bool = Field(default=False, description="Использовать S3 для хранения файлов")
    S3_BUCKET_NAME: str = Field(default="roadmate-files", description="Имя S3 бакета")
    S3_REGION: str = Field(default="us-east-1", description="Регион S3")
    S3_ACCESS_KEY_ID: str | None = Field(default=None, description="AWS Access Key")
    S3_SECRET_ACCESS_KEY: SecretStr | None = Field(default=None, description="AWS Secret Key")
    S3_ENDPOINT_URL: str | None = Field(default=None, description="Кастомный S3 эндпоинт")

    model_config = SettingsConfigDict(
        env_prefix="FILES_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class LocalizationSettings(BaseSettings):
    """Настройки локализации."""

    DEFAULT_LANGUAGE: str = Field(default="ru", description="Язык по умолчанию")
    SUPPORTED_LANGUAGES: list[str] = Field(
        default=["ru", "en"],
        description="Поддерживаемые языки"
    )

    # Провайдер переводов
    TRANSLATIONS_PROVIDER: str = Field(default="json", description="Провайдер переводов (json, gettext)")
    TRANSLATIONS_DIR: str = Field(default="./app/locales", description="Директория с переводами")

    # Формат даты и времени
    DATE_FORMAT: str = Field(default="%d.%m.%Y", description="Формат даты")
    DATETIME_FORMAT: str = Field(default="%d.%m.%Y %H:%M", description="Формат даты и времени")
    TIMEZONE: str = Field(default="Europe/Moscow", description="Часовой пояс")

    model_config = SettingsConfigDict(
        env_prefix="LOCALE_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class LoggingSettings(BaseSettings):
    """Настройки логирования."""

    # Уровень логирования
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # Формат логов
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Формат логов"
    )

    # Вывод в консоль
    LOG_CONSOLE_ENABLED: bool = Field(default=True, description="Выводить логи в консоль")
    LOG_CONSOLE_FORMAT: str | None = Field(default=None)

    # Вывод в файл
    LOG_FILE_ENABLED: bool = Field(default=False, description="Выводить логи в файл")
    LOG_FILE_PATH: str = Field(default="./logs/app.log", description="Путь к файлу логов")
    LOG_FILE_MAX_BYTES: int = Field(default=10 * 1024 * 1024, description="Максимальный размер файла")
    LOG_FILE_BACKUP_COUNT: int = Field(default=5, description="Количество резервных файлов")

    # Структурное логирование (JSON)
    LOG_JSON_ENABLED: bool = Field(default=False, description="Использовать JSON формат")

    # Отдельные логгеры
    LOG_SQL_ALCHEMY: bool = Field(default=False, description="Логировать SQL запросы")
    LOG_SQL_ECHO: bool = Field(default=False, description="Выводить SQL в консоль")

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class AppSettings(BaseSettings):
    """Основные настройки приложения."""

    # Настройки приложения
    APP_NAME: str = Field(default="RoadMate", description="Название приложения")
    APP_VERSION: str = Field(default="0.1.0", description="Версия приложения")
    APP_DESCRIPTION: str = Field(
        default="BlaBlaCar clone - сервис для поиска попутчиков",
        description="Описание приложения"
    )

    # Режим работы
    DEBUG: bool = Field(default=False, description="Режим отладки")
    ENVIRONMENT: str = Field(
        default="dev",
        description="Окружение (dev, test, prod)"
    )
    TESTING: bool = Field(default=False, description="Режим тестирования")

    # API настройки
    API_V1_PREFIX: str = Field(default="/api/v1", description="Префикс API v1")
    API_DOCS_URL: str | None = Field(default="/docs", description="URL документации")
    API_REDOC_URL: str | None = Field(default="/redoc", description="URL ReDoc")

    # Сервер
    HOST: str = Field(default="0.0.0.0", description="Хост для запуска")
    PORT: int = Field(default=8000, description="Порт для запуска")
    WORKERS: int = Field(default=4, description="Количество воркеров")

    # Прокси
    TRUSTED_HOSTS: list[str] = Field(
        default=["*"],
        description="Доверенные прокси"
    )

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


class Settings(BaseSettings):
    """
    Единая конфигурация приложения.

    Использование:
        from app.core.config import settings

        # Доступ к настройкам
        settings.database.DATABASE_URL
        settings.security.SECRET_KEY
        settings.app.APP_NAME
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=True,
        extra="ignore"
    )

    # Вложенные настройки по категориям
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    files: FilesSettings = Field(default_factory=FilesSettings)
    locale: LocalizationSettings = Field(default_factory=LocalizationSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    # Прямой доступ к часто используемым параметрам (для обратной совместимости)
    @property
    def APP_NAME(self) -> str:
        return self.app.APP_NAME

    @property
    def APP_VERSION(self) -> str:
        return self.app.APP_VERSION

    @property
    def DEBUG(self) -> bool:
        return self.app.DEBUG

    @property
    def ENVIRONMENT(self) -> str:
        return self.app.ENVIRONMENT

    @property
    def DATABASE_URL(self) -> str:
        return self.database.DATABASE_URL

    @property
    def SECRET_KEY(self) -> SecretStr:
        # Используем JWT настройки если доступны, иначе security
        return self.jwt.SECRET_KEY

    @property
    def ALGORITHM(self) -> str:
        return self.jwt.ALGORITHM

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.jwt.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def DEFAULT_LANGUAGE(self) -> str:
        return self.locale.DEFAULT_LANGUAGE

    @property
    def SUPPORTED_LANGUAGES(self) -> list[str]:
        return self.locale.SUPPORTED_LANGUAGES

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return self.cors.ORIGINS

    def is_development(self) -> bool:
        """Проверка режима разработки."""
        return self.app.ENVIRONMENT == "dev"

    def is_testing(self) -> bool:
        """Проверка режима тестирования."""
        return self.app.TESTING or self.app.ENVIRONMENT == "test"

    def is_production(self) -> bool:
        """Проверка режима продакшена."""
        return self.app.ENVIRONMENT == "prod"


@lru_cache
def get_settings() -> Settings:
    """
    Получение экземпляра настроек (cached).

    Returns:
        Settings: Экземпляр настроек
    """
    return Settings()


# Глобальный экземпляр настроек
settings = get_settings()

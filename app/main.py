"""
Основной файл FastAPI приложения.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import websocket
from app.api.v1.api_router import api_router
from app.core.config import settings
from app.db.session import create_tables

# Создание приложения
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API для сервиса совместных поездок",
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Настройте для production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Запуск при старте приложения."""
    await create_tables()


# Подключение роутеров
app.include_router(api_router)
app.include_router(websocket.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Корневой эндпоинт."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Проверка здоровья приложения."""
    return {"status": "healthy"}
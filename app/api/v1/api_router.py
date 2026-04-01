"""
Объединение всех API роутеров v1.
"""
from fastapi import APIRouter

from app.api.v1 import admin, auth, chat, notifications, requests, reviews, trips, users
from app.api.v1.users import settings as user_settings

api_router = APIRouter(prefix="/api/v1")

# Подключение доменных роутеров
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(user_settings.router, prefix="/users", tags=["Users"])
api_router.include_router(trips.router, prefix="/trips", tags=["Trips"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
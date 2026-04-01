"""
Роутер домена Users.
Эндпоинты:
- GET /{user_id} — просмотр профиля
- PUT /me — редактирование профиля
- PUT /me/avatar — загрузка аватара
- GET /me/rating — рейтинг пользователя
- PUT /me/preferences — настройки языка
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{user_id}")
async def get_user_profile(user_id: int) -> dict[str, str]:
    """Просмотр профиля пользователя."""
    return {"message": f"User profile {user_id}"}


@router.put("/me")
async def update_profile() -> dict[str, str]:
    """Редактирование своего профиля."""
    return {"message": "Update profile"}


@router.put("/me/avatar")
async def upload_avatar() -> dict[str, str]:
    """Загрузка аватара."""
    return {"message": "Upload avatar"}


@router.get("/me/rating")
async def get_user_rating() -> dict[str, str]:
    """Получение рейтинга пользователя."""
    return {"message": "User rating"}


@router.put("/me/preferences")
async def update_preferences() -> dict[str, str]:
    """Обновление настроек (язык и др.)."""
    return {"message": "Update preferences"}
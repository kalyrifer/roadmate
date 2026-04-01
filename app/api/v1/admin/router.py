"""
Роутер домена Admin (только для администраторов).
Эндпоинты:
- GET /users — управление пользователями
- GET /trips — управление поездками
- POST /users/{user_id}/block — блокировка пользователя
- GET /audit-logs — журнал аудита
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/users")
async def list_users() -> dict[str, str]:
    """Список пользователей (с фильтрацией)."""
    return {"message": "Admin list users"}


@router.get("/trips")
async def list_trips() -> dict[str, str]:
    """Список поездок (с модерацией)."""
    return {"message": "Admin list trips"}


@router.post("/users/{user_id}/block")
async def block_user(user_id: int) -> dict[str, str]:
    """Блокировка пользователя."""
    return {"message": f"Block user {user_id}"}


@router.get("/audit-logs")
async def get_audit_logs() -> dict[str, str]:
    """Журнал аудита действий."""
    return {"message": "Audit logs"}
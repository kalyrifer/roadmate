"""
Роутер домена Trips.
Эндпоинты:
- POST / — создание поездки
- GET / — список поездок с фильтрацией
- GET /{trip_id} — детали поездки
- PUT /{trip_id} — редактирование поездки
- DELETE /{trip_id} — удаление/отмена поездки
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_trip() -> dict[str, str]:
    """Создание новой поездки."""
    return {"message": "Create trip"}


@router.get("/")
async def list_trips() -> dict[str, str]:
    """Получение списка поездок с фильтрацией."""
    return {"message": "List trips"}


@router.get("/{trip_id}")
async def get_trip(trip_id: int) -> dict[str, str]:
    """Получение деталей поездки."""
    return {"message": f"Get trip {trip_id}"}


@router.put("/{trip_id}")
async def update_trip(trip_id: int) -> dict[str, str]:
    """Редактирование поездки."""
    return {"message": f"Update trip {trip_id}"}


@router.delete("/{trip_id}")
async def delete_trip(trip_id: int) -> dict[str, str]:
    """Удаление или отмена поездки."""
    return {"message": f"Delete trip {trip_id}"}
"""
Роутер для работы с уведомлениями (Notifications).

Эндпоинты:
- GET / — список уведомлений пользователя
- PUT /{notification_id}/read — отметить прочитанным
- PUT /read-all — массовая отметка прочитанными
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession, CurrentUserId
from app.models.notifications.model import NotificationType
from app.schemas.notifications.schemas import NotificationListResponse, NotificationResponse
from app.services.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    db: DbSession,
    current_user_id: CurrentUserId,
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Количество на странице"),
    is_read: Optional[bool] = Query(None, description="Фильтр по статусу прочтения"),
    type: Optional[NotificationType] = Query(None, description="Фильтр по типу уведомления"),
) -> NotificationListResponse:
    """
    Получение списка уведомлений текущего пользователя.
    
    Поддерживает пагинацию и фильтрацию по:
    - is_read: прочитано/не прочитано
    - type: тип уведомления
    """
    service = NotificationService(db)
    return await service.list_notifications(
        user_id=current_user_id,
        page=page,
        page_size=page_size,
        is_read=is_read,
        type=type,
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    db: DbSession,
    current_user_id: CurrentUserId,
) -> NotificationResponse:
    """
    Отметка уведомления как прочитанного.
    
    Только владелец уведомления может отметить его как прочитанное.
    """
    service = NotificationService(db)
    notification = await service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user_id,
    )
    
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено",
        )
    
    return notification


@router.put("/read-all")
async def mark_all_notifications_read(
    db: DbSession,
    current_user_id: CurrentUserId,
) -> dict[str, int]:
    """
    Массовая отметка всех уведомлений пользователя как прочитанных.
    
    Возвращает количество отмеченных уведомлений.
    """
    service = NotificationService(db)
    count = await service.mark_all_as_read(user_id=current_user_id)
    
    return {"marked_count": count}


@router.get("/unread-count")
async def get_unread_count(
    db: DbSession,
    current_user_id: CurrentUserId,
) -> dict[str, int]:
    """
    Получение количества непрочитанных уведомлений.
    """
    service = NotificationService(db)
    count = await service.get_unread_count(user_id=current_user_id)
    
    return {"unread_count": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    db: DbSession,
    current_user_id: CurrentUserId,
) -> dict[str, str]:
    """
    Удаление уведомления.
    
    Только владелец уведомления может удалить его.
    """
    service = NotificationService(db)
    deleted = await service.delete(
        notification_id=notification_id,
        user_id=current_user_id,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Уведомление не найдено",
        )
    
    return {"message": "Уведомление удалено"}

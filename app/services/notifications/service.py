"""
Service слой для работы с уведомлениями.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications.model import NotificationType
from app.repositories.notifications.repository import NotificationRepository
from app.schemas.notifications.schemas import (
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
    NotificationStats,
)


class NotificationService:
    """Service для работы с уведомлениями."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = NotificationRepository(session)

    async def create_notification(
        self,
        data: NotificationCreate,
    ) -> NotificationResponse:
        """Создание уведомления."""
        notification = await self.repository.create(
            user_id=data.user_id,
            type=data.type,
            title=data.title,
            message=data.message,
            related_trip_id=data.related_trip_id,
            related_request_id=data.related_request_id,
        )
        return NotificationResponse.model_validate(notification)

    async def get_notification(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> Optional[NotificationResponse]:
        """Получение уведомления по ID."""
        notification = await self.repository.get_by_id_for_user(
            notification_id, user_id
        )
        if notification:
            return NotificationResponse.model_validate(notification)
        return None

    async def list_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_read: Optional[bool] = None,
        type: Optional[NotificationType] = None,
    ) -> NotificationListResponse:
        """Получение списка уведомлений пользователя."""
        offset = (page - 1) * page_size

        notifications, total = await self.repository.list_by_user(
            user_id=user_id,
            is_read=is_read,
            type=type,
            limit=page_size,
            offset=offset,
        )

        unread_count = await self.repository.get_unread_count(user_id)

        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in notifications],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            stats=NotificationStats(
                unread_count=unread_count,
                total_count=total,
            ),
        )

    async def mark_as_read(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> Optional[NotificationResponse]:
        """Отметка уведомления как прочитанного."""
        notification = await self.repository.mark_as_read(notification_id, user_id)
        if notification:
            return NotificationResponse.model_validate(notification)
        return None

    async def mark_all_as_read(
        self,
        user_id: UUID,
    ) -> int:
        """Отметка всех уведомлений как прочитанных."""
        return await self.repository.mark_all_as_read(user_id)

    async def get_unread_count(self, user_id: UUID) -> int:
        """Получение количества непрочитанных уведомлений."""
        return await self.repository.get_unread_count(user_id)


class NotificationEventService:
    """Service для создания уведомлений по событиям домена."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = NotificationRepository(session)

    async def notify_new_request(
        self,
        driver_id: UUID,
        passenger_name: str,
        trip_id: UUID,
        request_id: UUID,
        from_city: str,
        to_city: str,
    ) -> NotificationResponse:
        """Уведомление водителю о новом запросе."""
        notification = await self.repository.create(
            user_id=driver_id,
            type=NotificationType.REQUEST_NEW,
            title="Новый запрос на бронирование",
            message=f"Пользователь {passenger_name} хочет забронировать место в поездке из {from_city} в {to_city}.",
            related_trip_id=trip_id,
            related_request_id=request_id,
        )
        return NotificationResponse.model_validate(notification)

    async def notify_request_confirmed(
        self,
        passenger_id: UUID,
        driver_name: str,
        trip_id: UUID,
        request_id: UUID,
        from_city: str,
        to_city: str,
    ) -> NotificationResponse:
        """Уведомление пассажиру о подтверждении запроса."""
        notification = await self.repository.create(
            user_id=passenger_id,
            type=NotificationType.REQUEST_CONFIRMED,
            title="Запрос подтверждён",
            message=f"Водитель {driver_name} подтвердил ваш запрос на бронирование поездки из {from_city} в {to_city}.",
            related_trip_id=trip_id,
            related_request_id=request_id,
        )
        return NotificationResponse.model_validate(notification)

    async def notify_request_rejected(
        self,
        passenger_id: UUID,
        driver_name: str,
        trip_id: UUID,
        request_id: UUID,
        from_city: str,
        to_city: str,
        reason: Optional[str] = None,
    ) -> NotificationResponse:
        """Уведомление пассажиру об отклонении запроса."""
        message = f"Водитель {driver_name} отклонил ваш запрос на бронирование поездки из {from_city} в {to_city}."
        if reason:
            message += f"\nПричина: {reason}"

        notification = await self.repository.create(
            user_id=passenger_id,
            type=NotificationType.REQUEST_REJECTED,
            title="Запрос отклонён",
            message=message,
            related_trip_id=trip_id,
            related_request_id=request_id,
        )
        return NotificationResponse.model_validate(notification)

    async def notify_request_cancelled(
        self,
        user_id: UUID,
        trip_id: UUID,
        request_id: UUID,
        from_city: str,
        to_city: str,
        cancelled_by: str,
    ) -> NotificationResponse:
        """Уведомление об отмене запроса."""
        who = "пассажир" if cancelled_by == "passenger" else "водитель"
        notification = await self.repository.create(
            user_id=user_id,
            type=NotificationType.REQUEST_CANCELLED,
            title="Запрос отменён",
            message=f"Запрос на бронирование поездки из {from_city} в {to_city} был отменён ({who} отменил бронирование).",
            related_trip_id=trip_id,
            related_request_id=request_id,
        )
        return NotificationResponse.model_validate(notification)

    async def notify_trip_cancelled(
        self,
        user_id: UUID,
        trip_id: UUID,
        from_city: str,
        to_city: str,
        reason: Optional[str] = None,
    ) -> NotificationResponse:
        """Уведомление об отмене поездки."""
        message = f"Поездка из {from_city} в {to_city} была отменена."
        if reason:
            message += f"\nПричина: {reason}"

        notification = await self.repository.create(
            user_id=user_id,
            type=NotificationType.TRIP_CANCELLED,
            title="Поездка отменена",
            message=message,
            related_trip_id=trip_id,
        )
        return NotificationResponse.model_validate(notification)

    async def notify_trip_completed(
        self,
        user_id: UUID,
        trip_id: UUID,
        from_city: str,
        to_city: str,
    ) -> NotificationResponse:
        """Уведомление о завершении поездки."""
        notification = await self.repository.create(
            user_id=user_id,
            type=NotificationType.TRIP_COMPLETED,
            title="Поездка завершена",
            message=f"Поездка из {from_city} в {to_city} завершена. Спасибо за использование RoadMate!",
            related_trip_id=trip_id,
        )
        return NotificationResponse.model_validate(notification)

    async def notify_new_message(
        self,
        recipient_id: UUID,
        sender_name: str,
        trip_id: UUID,
        message_preview: str,
    ) -> NotificationResponse:
        """Уведомление о новом сообщении."""
        preview = message_preview[:100] + "..." if len(message_preview) > 100 else message_preview

        notification = await self.repository.create(
            user_id=recipient_id,
            type=NotificationType.MESSAGE_NEW,
            title=f"Новое сообщение от {sender_name}",
            message=preview,
            related_trip_id=trip_id,
        )
        return NotificationResponse.model_validate(notification)

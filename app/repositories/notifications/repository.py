"""
Repository слой для работы с уведомлениями.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications.model import Notification, NotificationType


class NotificationRepository:
    """Repository для работы с уведомлениями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        type: NotificationType,
        title: str,
        message: str,
        related_trip_id: Optional[UUID] = None,
        related_request_id: Optional[UUID] = None,
        related_conversation_id: Optional[UUID] = None,
    ) -> Notification:
        """Создание нового уведомления."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            related_trip_id=related_trip_id,
            related_request_id=related_request_id,
            related_conversation_id=related_conversation_id,
        )
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Получение уведомления по ID."""
        result = await self.session.execute(
            select(Notification)
            .where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> Optional[Notification]:
        """Получение уведомления по ID для конкретного пользователя."""
        result = await self.session.execute(
            select(Notification)
            .where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        is_read: Optional[bool] = None,
        type: Optional[NotificationType] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        """Получение списка уведомлений пользователя."""
        conditions = [Notification.user_id == user_id]

        if is_read is not None:
            conditions.append(Notification.is_read == is_read)

        if type is not None:
            conditions.append(Notification.type == type)

        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(Notification.id))
            .where(and_(*conditions))
        )
        total = count_result.scalar()

        # Получаем уведомления
        result = await self.session.execute(
            select(Notification)
            .where(and_(*conditions))
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        notifications = list(result.scalars().all())

        return notifications, total

    async def get_unread_count(self, user_id: UUID) -> int:
        """Получение количества непрочитанных уведомлений."""
        result = await self.session.execute(
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
            )
        )
        return result.scalar() or 0

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        """Отметка уведомления как прочитанного."""
        from datetime import datetime, timezone

        notification = await self.get_by_id_for_user(notification_id, user_id)
        if not notification:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(notification)

        return notification

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Отметка всех уведомлений пользователя как прочитанных."""
        from datetime import datetime, timezone

        result = await self.session.execute(
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
            )
        )
        notifications = list(result.scalars().all())

        count = 0
        now = datetime.now(timezone.utc)
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            count += 1

        if count > 0:
            await self.session.flush()

        return count

    async def delete(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Удаление уведомления по ID для конкретного пользователя."""
        notification = await self.get_by_id_for_user(notification_id, user_id)
        if not notification:
            return False

        await self.session.delete(notification)
        await self.session.flush()
        return True

    async def delete_old_notifications(self, days: int = 90) -> int:
        """Удаление старых прочитанных уведомлений (для очистки)."""
        from datetime import datetime, timedelta, timezone

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.session.execute(
            select(Notification)
            .where(
                and_(
                    Notification.is_read == True,
                    Notification.created_at < cutoff_date,
                )
            )
        )
        notifications = list(result.scalars().all())

        count = len(notifications)
        for notification in notifications:
            await self.session.delete(notification)

        if count > 0:
            await self.session.flush()

        return count

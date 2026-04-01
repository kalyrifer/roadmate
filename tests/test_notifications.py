"""
Тесты для модуля уведомлений (Notifications).
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.models.notifications.model import Notification, NotificationType
from app.services.notifications.service import NotificationService, NotificationEventService
from app.schemas.notifications.schemas import NotificationCreate


# === Fixtures ===
@pytest.fixture
def mock_session():
    """Мок сессии БД."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def service(mock_session):
    """Сервис с моком сессии."""
    return NotificationService(mock_session)


@pytest.fixture
def event_service(mock_session):
    """Event-сервис с моком сессии."""
    return NotificationEventService(mock_session)


@pytest.fixture
def mock_notification():
    """Мок уведомления."""
    notification = MagicMock(spec=Notification)
    notification.id = uuid4()
    notification.user_id = uuid4()
    notification.type = NotificationType.REQUEST_NEW
    notification.title = "Тестовое уведомление"
    notification.message = "Тестовое сообщение"
    notification.is_read = False
    notification.related_trip_id = None
    notification.related_request_id = None
    notification.read_at = None
    notification.created_at = None
    return notification


# === Тесты создания уведомления ===
@pytest.mark.asyncio
async def test_create_notification_success(service, mock_session):
    """Успешное создание уведомления."""
    user_id = uuid4()
    data = NotificationCreate(
        user_id=user_id,
        type=NotificationType.REQUEST_NEW,
        title="Новый запрос",
        message="Поступил новый запрос на бронирование",
    )
    
    # Мок репозитория
    mock_notification = MagicMock(spec=Notification)
    mock_notification.id = uuid4()
    mock_notification.user_id = user_id
    mock_notification.type = NotificationType.REQUEST_NEW
    mock_notification.title = "Новый запрос"
    mock_notification.message = "Поступил новый запрос на бронирование"
    mock_notification.is_read = False
    mock_notification.related_trip_id = None
    mock_notification.related_request_id = None
    mock_notification.created_at = None
    
    service.repository.create = AsyncMock(return_value=mock_notification)
    
    result = await service.create_notification(data)
    
    assert result.type == NotificationType.REQUEST_NEW
    assert result.title == "Новый запрос"
    assert result.is_read is False
    service.repository.create.assert_called_once()


# === Тесты получения списка уведомлений ===
@pytest.mark.asyncio
async def test_list_notifications_empty(service, mock_session):
    """Пустой список уведомлений."""
    user_id = uuid4()
    
    service.repository.list_by_user = AsyncMock(return_value=([], 0))
    service.repository.get_unread_count = AsyncMock(return_value=0)
    
    result = await service.list_notifications(user_id=user_id)
    
    assert result.total == 0
    assert len(result.items) == 0
    assert result.stats.unread_count == 0


@pytest.mark.asyncio
async def test_list_notifications_with_items(service, mock_session):
    """Список уведомлений с элементами."""
    user_id = uuid4()
    
    # Создаем мок уведомления
    notification = MagicMock(spec=Notification)
    notification.id = uuid4()
    notification.user_id = user_id
    notification.type = NotificationType.REQUEST_NEW
    notification.title = "Новый запрос"
    notification.message = "Поступил новый запрос"
    notification.is_read = False
    notification.related_trip_id = None
    notification.related_request_id = None
    notification.read_at = None
    notification.created_at = None
    
    service.repository.list_by_user = AsyncMock(return_value=([notification], 1))
    service.repository.get_unread_count = AsyncMock(return_value=1)
    
    result = await service.list_notifications(user_id=user_id)
    
    assert result.total == 1
    assert len(result.items) == 1
    assert result.stats.unread_count == 1


@pytest.mark.asyncio
async def test_list_notifications_with_filter_is_read(service, mock_session):
    """Фильтрация уведомлений по статусу прочтения."""
    user_id = uuid4()
    
    service.repository.list_by_user = AsyncMock(return_value=([], 0))
    service.repository.get_unread_count = AsyncMock(return_value=0)
    
    result = await service.list_notifications(
        user_id=user_id,
        is_read=True,
    )
    
    service.repository.list_by_user.assert_called_once()
    call_args = service.repository.list_by_user.call_args
    assert call_args.kwargs['is_read'] is True


@pytest.mark.asyncio
async def test_list_notifications_with_filter_type(service, mock_session):
    """Фильтрация уведомлений по типу."""
    user_id = uuid4()
    
    service.repository.list_by_user = AsyncMock(return_value=([], 0))
    service.repository.get_unread_count = AsyncMock(return_value=0)
    
    result = await service.list_notifications(
        user_id=user_id,
        type=NotificationType.REQUEST_NEW,
    )
    
    service.repository.list_by_user.assert_called_once()
    call_args = service.repository.list_by_user.call_args
    assert call_args.kwargs['type'] == NotificationType.REQUEST_NEW


# === Тесты пагинации ===
@pytest.mark.asyncio
async def test_list_notifications_pagination(service, mock_session):
    """Пагинация уведомлений."""
    user_id = uuid4()
    
    service.repository.list_by_user = AsyncMock(return_value=([], 0))
    service.repository.get_unread_count = AsyncMock(return_value=0)
    
    result = await service.list_notifications(
        user_id=user_id,
        page=2,
        page_size=10,
    )
    
    call_args = service.repository.list_by_user.call_args
    assert call_args.kwargs['limit'] == 10
    assert call_args.kwargs['offset'] == 10  # (page-1) * page_size = (2-1) * 10


# === Тесты отметки уведомления как прочитанного ===
@pytest.mark.asyncio
async def test_mark_as_read_success(service, mock_session):
    """Успешная отметка уведомления как прочитанного."""
    user_id = uuid4()
    notification_id = uuid4()
    
    notification = MagicMock(spec=Notification)
    notification.id = notification_id
    notification.user_id = user_id
    notification.type = NotificationType.REQUEST_NEW
    notification.title = "Тест"
    notification.message = "Тест"
    notification.is_read = True
    notification.related_trip_id = None
    notification.related_request_id = None
    notification.read_at = None
    notification.created_at = None
    
    service.repository.mark_as_read = AsyncMock(return_value=notification)
    
    result = await service.mark_as_read(notification_id, user_id)
    
    assert result is not None
    assert result.is_read is True


@pytest.mark.asyncio
async def test_mark_as_read_not_found(service, mock_session):
    """Отметка несуществующего уведомления."""
    user_id = uuid4()
    notification_id = uuid4()
    
    service.repository.mark_as_read = AsyncMock(return_value=None)
    
    result = await service.mark_as_read(notification_id, user_id)
    
    assert result is None


# === Тесты массовой отметки ===
@pytest.mark.asyncio
async def test_mark_all_as_read(service, mock_session):
    """Массовая отметка всех уведомлений."""
    user_id = uuid4()
    
    service.repository.mark_all_as_read = AsyncMock(return_value=5)
    
    result = await service.mark_all_as_read(user_id)
    
    assert result == 5
    service.repository.mark_all_as_read.assert_called_once_with(user_id)


# === Тесты получения количества непрочитанных ===
@pytest.mark.asyncio
async def test_get_unread_count(service, mock_session):
    """Получение количества непрочитанных уведомлений."""
    user_id = uuid4()
    
    service.repository.get_unread_count = AsyncMock(return_value=3)
    
    result = await service.get_unread_count(user_id)
    
    assert result == 3
    service.repository.get_unread_count.assert_called_once_with(user_id)


# === Тесты event-сервиса ===
@pytest.mark.asyncio
async def test_notify_new_request(event_service, mock_session):
    """Уведомление о новом запросе."""
    driver_id = uuid4()
    trip_id = uuid4()
    request_id = uuid4()
    
    notification = MagicMock(spec=Notification)
    notification.id = uuid4()
    notification.user_id = driver_id
    notification.type = NotificationType.REQUEST_NEW
    notification.title = "Новый запрос на бронирование"
    notification.message = "Пользователь John Doe хочет забронировать место в поездке из Moscow в Saint Petersburg."
    notification.is_read = False
    notification.related_trip_id = trip_id
    notification.related_request_id = request_id
    notification.created_at = None
    
    event_service.repository.create = AsyncMock(return_value=notification)
    
    result = await event_service.notify_new_request(
        driver_id=driver_id,
        passenger_name="John Doe",
        trip_id=trip_id,
        request_id=request_id,
        from_city="Moscow",
        to_city="Saint Petersburg",
    )
    
    assert result.type == NotificationType.REQUEST_NEW
    event_service.repository.create.assert_called_once()
    call_kwargs = event_service.repository.create.call_args.kwargs
    assert call_kwargs['type'] == NotificationType.REQUEST_NEW
    assert call_kwargs['related_trip_id'] == trip_id
    assert call_kwargs['related_request_id'] == request_id


@pytest.mark.asyncio
async def test_notify_request_confirmed(event_service, mock_session):
    """Уведомление о подтверждении запроса."""
    passenger_id = uuid4()
    trip_id = uuid4()
    request_id = uuid4()
    
    notification = MagicMock(spec=Notification)
    notification.id = uuid4()
    notification.user_id = passenger_id
    notification.type = NotificationType.REQUEST_CONFIRMED
    
    event_service.repository.create = AsyncMock(return_value=notification)
    
    result = await event_service.notify_request_confirmed(
        passenger_id=passenger_id,
        driver_name="Jane Doe",
        trip_id=trip_id,
        request_id=request_id,
        from_city="Moscow",
        to_city="Saint Petersburg",
    )
    
    assert result.type == NotificationType.REQUEST_CONFIRMED


@pytest.mark.asyncio
async def test_notify_request_rejected(event_service, mock_session):
    """Уведомление об отклонении запроса."""
    passenger_id = uuid4()
    trip_id = uuid4()
    request_id = uuid4()
    
    notification = MagicMock(spec=Notification)
    notification.id = uuid4()
    notification.user_id = passenger_id
    notification.type = NotificationType.REQUEST_REJECTED
    
    event_service.repository.create = AsyncMock(return_value=notification)
    
    result = await event_service.notify_request_rejected(
        passenger_id=passenger_id,
        driver_name="Jane Doe",
        trip_id=trip_id,
        request_id=request_id,
        from_city="Moscow",
        to_city="Saint Petersburg",
        reason="No seats available",
    )
    
    assert result.type == NotificationType.REQUEST_REJECTED
    call_kwargs = event_service.repository.create.call_args.kwargs
    assert "No seats available" in call_kwargs['message']


@pytest.mark.asyncio
async def test_notify_trip_cancelled(event_service, mock_session):
    """Уведомление об отмене поездки."""
    user_id = uuid4()
    trip_id = uuid4()
    
    notification = MagicMock(spec=Notification)
    notification.id = uuid4()
    notification.user_id = user_id
    notification.type = NotificationType.TRIP_CANCELLED
    
    event_service.repository.create = AsyncMock(return_value=notification)
    
    result = await event_service.notify_trip_cancelled(
        user_id=user_id,
        trip_id=trip_id,
        from_city="Moscow",
        to_city="Saint Petersburg",
    )
    
    assert result.type == NotificationType.TRIP_CANCELLED


@pytest.mark.asyncio
async def test_notify_new_message(event_service, mock_session):
    """Уведомление о новом сообщении."""
    recipient_id = uuid4()
    trip_id = uuid4()
    
    notification = MagicMock(spec=Notification)
    notification.id = uuid4()
    notification.user_id = recipient_id
    notification.type = NotificationType.MESSAGE_NEW
    
    event_service.repository.create = AsyncMock(return_value=notification)
    
    result = await event_service.notify_new_message(
        recipient_id=recipient_id,
        sender_name="John Doe",
        trip_id=trip_id,
        message_preview="Привет! Как дела?",
    )
    
    assert result.type == NotificationType.MESSAGE_NEW
    call_kwargs = event_service.repository.create.call_args.kwargs
    assert call_kwargs['related_trip_id'] == trip_id

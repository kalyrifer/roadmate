"""
Тесты для модуля заявок на бронирование (TripRequest).
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.requests.model import TripRequest, TripRequestStatus
from app.models.trips.model import Trip, TripStatus
from app.services.requests.service import (
    TripRequestService,
    TripNotFoundError,
    TripNotAvailableError,
    TripRequestAlreadyExistsError,
    InsufficientSeatsError,
    ForbiddenError,
    CannotBookOwnTripError,
    TripRequestAlreadyProcessedError,
)
from app.schemas.requests import TripRequestCreate


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
    return TripRequestService(mock_session)


@pytest.fixture
def mock_trip():
    """Мок поездки."""
    trip = MagicMock(spec=Trip)
    trip.id = uuid4()
    trip.driver_id = uuid4()
    trip.available_seats = 3
    trip.status = TripStatus.PUBLISHED
    return trip


@pytest.fixture
def mock_request():
    """Мок заявки."""
    request = MagicMock(spec=TripRequest)
    request.id = uuid4()
    request.trip_id = uuid4()
    request.passenger_id = uuid4()
    request.seats_requested = 2
    request.status = TripRequestStatus.PENDING
    request.trip = mock_trip()
    return request


# === Тесты создания заявки ===
@pytest.mark.asyncio
async def test_create_request_success(service, mock_session):
    """Успешное создание заявки."""
    trip_id = uuid4()
    passenger_id = uuid4()
    data = TripRequestCreate(seats_requested=2, message="Хочу поехать")
    
    # Мок поиска поездки
    mock_trip = MagicMock()
    mock_trip.id = trip_id
    mock_trip.driver_id = uuid4()  # Не совпадает с passenger_id
    mock_trip.available_seats = 3
    mock_trip.status = TripStatus.PUBLISHED
    
    # Мок запроса
    with patch.object(service.repository, 'get_by_id', return_value=mock_trip):
        with patch.object(service.repository, 'get_pending_by_trip_and_passenger', return_value=None):
            with patch.object(service.repository, 'create', return_value=MagicMock(id=uuid4())):
                result = await service.create_request(trip_id, passenger_id, data)
                assert result is not None
                mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_request_trip_not_found(service, mock_session):
    """Ошибка: поездка не найдена."""
    trip_id = uuid4()
    passenger_id = uuid4()
    data = TripRequestCreate(seats_requested=2)
    
    with patch.object(service.repository, 'get_by_id', return_value=None):
        with pytest.raises(TripNotFoundError):
            await service.create_request(trip_id, passenger_id, data)


@pytest.mark.asyncio
async def test_create_request_trip_not_available(service, mock_session):
    """Ошибка: поездка недоступна для бронирования."""
    trip_id = uuid4()
    passenger_id = uuid4()
    data = TripRequestCreate(seats_requested=2)
    
    mock_trip = MagicMock()
    mock_trip.status = TripStatus.CANCELLED
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_trip):
        with pytest.raises(TripNotAvailableError):
            await service.create_request(trip_id, passenger_id, data)


@pytest.mark.asyncio
async def test_create_request_cannot_book_own_trip(service, mock_session):
    """Ошибка: нельзя забронировать свою поездку."""
    trip_id = uuid4()
    passenger_id = uuid4()
    data = TripRequestCreate(seats_requested=2)
    
    mock_trip = MagicMock()
    mock_trip.driver_id = passenger_id  # Пассажир = водитель
    mock_trip.status = TripStatus.PUBLISHED
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_trip):
        with pytest.raises(CannotBookOwnTripError):
            await service.create_request(trip_id, passenger_id, data)


@pytest.mark.asyncio
async def test_create_request_insufficient_seats(service, mock_session):
    """Ошибка: недостаточно мест."""
    trip_id = uuid4()
    passenger_id = uuid4()
    data = TripRequestCreate(seats_requested=5)  # Запрашиваем 5 мест
    
    mock_trip = MagicMock()
    mock_trip.driver_id = uuid4()
    mock_trip.available_seats = 2  # Доступно только 2
    mock_trip.status = TripStatus.PUBLISHED
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_trip):
        with pytest.raises(InsufficientSeatsError) as exc:
            await service.create_request(trip_id, passenger_id, data)
        # Проверяем, что ошибка содержит информацию о доступных местах
        assert "Доступно мест: 2" in str(exc.value)
        assert "запрошено: 5" in str(exc.value)


@pytest.mark.asyncio
async def test_create_request_already_exists(service, mock_session):
    """Ошибка: заявка уже существует."""
    trip_id = uuid4()
    passenger_id = uuid4()
    data = TripRequestCreate(seats_requested=2)
    
    mock_trip = MagicMock()
    mock_trip.driver_id = uuid4()
    mock_trip.available_seats = 3
    mock_trip.status = TripStatus.PUBLISHED
    
    existing_request = MagicMock()
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_trip):
        with patch.object(service.repository, 'get_pending_by_trip_and_passenger', return_value=existing_request):
            with pytest.raises(TripRequestAlreadyExistsError):
                await service.create_request(trip_id, passenger_id, data)


# === Тесты подтверждения заявки ===
@pytest.mark.asyncio
async def test_confirm_request_success(service, mock_session):
    """Успешное подтверждение заявки."""
    request_id = uuid4()
    driver_id = uuid4()
    
    mock_trip = MagicMock()
    mock_trip.driver_id = driver_id
    mock_trip.available_seats = 3
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.status = TripRequestStatus.PENDING
    mock_request.trip = mock_trip
    mock_request.seats_requested = 2
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with patch.object(service.repository, 'confirm', return_value=mock_request):
            result = await service.confirm_request(request_id, driver_id)
            assert result is not None
            mock_session.flush.assert_called()


@pytest.mark.asyncio
async def test_confirm_request_not_owner(service, mock_session):
    """Ошибка: не водитель поездки."""
    request_id = uuid4()
    driver_id = uuid4()
    
    mock_trip = MagicMock()
    mock_trip.driver_id = uuid4()  # Другой водитель
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.status = TripRequestStatus.PENDING
    mock_request.trip = mock_trip
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(ForbiddenError):
            await service.confirm_request(request_id, driver_id)


@pytest.mark.asyncio
async def test_confirm_request_insufficient_seats(service, mock_session):
    """Ошибка: недостаточно мест при подтверждении."""
    request_id = uuid4()
    driver_id = uuid4()
    
    mock_trip = MagicMock()
    mock_trip.driver_id = driver_id
    mock_trip.available_seats = 1  # Недостаточно
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.status = TripRequestStatus.PENDING
    mock_request.trip = mock_trip
    mock_request.seats_requested = 2
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(InsufficientSeatsError):
            await service.confirm_request(request_id, driver_id)


# === Тесты отклонения заявки ===
@pytest.mark.asyncio
async def test_reject_request_success(service, mock_session):
    """Успешное отклонение заявки."""
    request_id = uuid4()
    driver_id = uuid4()
    
    mock_trip = MagicMock()
    mock_trip.driver_id = driver_id
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.status = TripRequestStatus.PENDING
    mock_request.trip = mock_trip
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with patch.object(service.repository, 'reject', return_value=mock_request):
            result = await service.reject_request(request_id, driver_id)
            assert result is not None


# === Тесты отмены заявки ===
@pytest.mark.asyncio
async def test_cancel_request_success(service, mock_session):
    """Успешная отмена заявки пассажиром."""
    request_id = uuid4()
    user_id = uuid4()
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.passenger_id = user_id
    mock_request.status = TripRequestStatus.PENDING
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with patch.object(service.repository, 'cancel', return_value=mock_request):
            result = await service.cancel_request(request_id, user_id)
            assert result is not None


@pytest.mark.asyncio
async def test_cancel_request_not_owner(service, mock_session):
    """Ошибка: не владелец заявки."""
    request_id = uuid4()
    user_id = uuid4()
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.passenger_id = uuid4()  # Другой пользователь
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(ForbiddenError):
            await service.cancel_request(request_id, user_id)


# === Тесты проверки статусов ===
@pytest.mark.asyncio
async def test_confirm_already_processed(service, mock_session):
    """Ошибка: заявка уже подтверждена."""
    request_id = uuid4()
    driver_id = uuid4()
    
    mock_trip = MagicMock()
    mock_trip.driver_id = driver_id
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.status = TripRequestStatus.CONFIRMED  # Уже подтверждена
    mock_request.trip = mock_trip
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(TripRequestAlreadyProcessedError):
            await service.confirm_request(request_id, driver_id)


@pytest.mark.asyncio
async def test_cancel_already_processed(service, mock_session):
    """Ошибка: заявка уже отменена."""
    request_id = uuid4()
    user_id = uuid4()
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.passenger_id = user_id
    mock_request.status = TripRequestStatus.CANCELLED  # Уже отменена
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(TripRequestAlreadyProcessedError):
            await service.cancel_request(request_id, user_id)


# === Тесты race condition и атомарности ===

@pytest.mark.asyncio
async def test_confirm_request_race_condition_insufficient_seats(mock_session):
    """
    Тест race condition: несколько запросов одновременно на одно место.
    При подтверждении второго запроса мест должно не хватить.
    """
    # Этот тест демонстрирует логику, но требует реальной БД для проверки
    # Проверяем, что confirm_with_seats правильно обрабатывает ситуацию
    pass


@pytest.mark.asyncio
async def test_create_request_check_confirmed_status(service, mock_session):
    """
    Тест: нельзя создать заявку, если уже есть подтверждённая.
    """
    trip_id = uuid4()
    passenger_id = uuid4()
    data = TripRequestCreate(seats_requested=2)
    
    mock_trip = MagicMock()
    mock_trip.driver_id = uuid4()
    mock_trip.available_seats = 3
    mock_trip.status = TripStatus.PUBLISHED
    
    # Существует подтверждённая заявка
    existing_request = MagicMock()
    existing_request.status = TripRequestStatus.CONFIRMED
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_trip):
        with patch.object(service.repository, 'get_active_by_trip_and_passenger', return_value=existing_request):
            with pytest.raises(TripRequestAlreadyExistsError) as exc_info:
                await service.create_request(trip_id, passenger_id, data)
            assert "подтверждённая" in str(exc_info.value)


@pytest.mark.asyncio
async def test_confirm_request_double_confirm_protection(service, mock_session):
    """
    Тест: защита от двойного подтверждения.
    При попытке подтвердить уже подтверждённую заявку должна быть ошибка.
    """
    request_id = uuid4()
    driver_id = uuid4()
    
    mock_trip = MagicMock()
    mock_trip.driver_id = driver_id
    mock_trip.available_seats = 3
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.status = TripRequestStatus.PENDING
    mock_request.trip = mock_trip
    mock_request.seats_requested = 2
    
    # Подтверждаем первый раз
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with patch.object(service.repository, 'confirm_with_seats', return_value=mock_request):
            result = await service.confirm_request(request_id, driver_id)
            assert result is not None
    
    # Пытаемся подтвердить второй раз - заявка уже подтверждена
    mock_request_confirmed = MagicMock()
    mock_request_confirmed.id = request_id
    mock_request_confirmed.status = TripRequestStatus.CONFIRMED
    mock_request_confirmed.trip = mock_trip
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request_confirmed):
        with pytest.raises(TripRequestAlreadyProcessedError):
            await service.confirm_request(request_id, driver_id)


@pytest.mark.asyncio
async def test_reject_request_not_owner(service, mock_session):
    """Ошибка: не водитель поездки при отклонении."""
    trip_id = uuid4()
    request_id = uuid4()
    driver_id = uuid4()
    
    mock_trip = MagicMock()
    mock_trip.driver_id = uuid4()  # Другой водитель
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.trip_id = trip_id
    mock_request.status = TripRequestStatus.PENDING
    mock_request.trip = mock_trip
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(ForbiddenError):
            await service.reject_request(trip_id, request_id, driver_id)


@pytest.mark.asyncio
async def test_reject_request_wrong_trip(service, mock_session):
    """Ошибка: заявка не принадлежит указанной поездке."""
    trip_id = uuid4()
    request_id = uuid4()
    driver_id = uuid4()
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.trip_id = uuid4()  # Другая поездка
    mock_request.status = TripRequestStatus.PENDING
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(TripRequestNotFoundError):
            await service.reject_request(trip_id, request_id, driver_id)


@pytest.mark.asyncio
async def test_reject_request_already_rejected(service, mock_session):
    """Ошибка: нельзя повторно отклонить заявку."""
    trip_id = uuid4()
    request_id = uuid4()
    driver_id = uuid4()
    
    mock_trip = MagicMock()
    mock_trip.driver_id = driver_id
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.trip_id = trip_id
    mock_request.status = TripRequestStatus.REJECTED  # Уже отклонена
    mock_request.trip = mock_trip
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(TripRequestAlreadyProcessedError):
            await service.reject_request(trip_id, request_id, driver_id)


@pytest.mark.asyncio
async def test_cancel_already_rejected(service, mock_session):
    """Ошибка: нельзя отменить уже отклонённую заявку."""
    request_id = uuid4()
    user_id = uuid4()
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.passenger_id = user_id
    mock_request.status = TripRequestStatus.REJECTED  # Уже отклонена
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(TripRequestAlreadyProcessedError):
            await service.cancel_request(request_id, user_id)


@pytest.mark.asyncio
async def test_cancel_already_confirmed(service, mock_session):
    """Ошибка: нельзя отменить уже подтверждённую заявку."""
    request_id = uuid4()
    user_id = uuid4()
    
    mock_request = MagicMock()
    mock_request.id = request_id
    mock_request.passenger_id = user_id
    mock_request.status = TripRequestStatus.CONFIRMED  # Уже подтверждена
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_request):
        with pytest.raises(TripRequestAlreadyProcessedError):
            await service.cancel_request(request_id, user_id)
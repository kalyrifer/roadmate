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
        with pytest.raises(InsufficientSeatsError):
            await service.create_request(trip_id, passenger_id, data)


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
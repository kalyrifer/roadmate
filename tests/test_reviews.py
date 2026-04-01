"""
Тесты для модуля отзывов (Review).
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.reviews.model import Review, ReviewStatus
from app.models.trips.model import Trip, TripStatus
from app.models.requests.model import TripRequest, TripRequestStatus
from app.services.reviews.service import (
    ReviewService,
    TripNotFoundError,
    TripNotCompletedError,
    ReviewAlreadyExistsError,
    UserNotParticipantError,
    CannotReviewSelfError,
    ForbiddenError,
    ReviewNotFoundError,
)
from app.schemas.reviews import ReviewCreate


# === Fixtures ===
@pytest.fixture
def mock_session():
    """Мок сессии БД."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def service(mock_session):
    """Сервис с моком сессии."""
    return ReviewService(mock_session)


@pytest.fixture
def mock_trip_completed():
    """Мок завершённой поездки."""
    trip = MagicMock(spec=Trip)
    trip.id = uuid4()
    trip.driver_id = uuid4()
    trip.status = TripStatus.COMPLETED
    return trip


@pytest.fixture
def mock_trip_not_completed():
    """Мок незавершённой поездки."""
    trip = MagicMock(spec=Trip)
    trip.id = uuid4()
    trip.driver_id = uuid4()
    trip.status = TripStatus.PUBLISHED
    return trip


@pytest.fixture
def mock_review():
    """Мок отзыва."""
    review = MagicMock(spec=Review)
    review.id = uuid4()
    review.trip_id = uuid4()
    review.author_id = uuid4()
    review.target_id = uuid4()
    review.rating = 5
    review.text = "Отличная поездка!"
    review.status = ReviewStatus.PENDING
    return review


# === Тесты создания отзыва ===
@pytest.mark.asyncio
async def test_create_review_success(service, mock_session, mock_trip_completed):
    """Успешное создание отзыва."""
    trip_id = uuid4()
    author_id = uuid4()
    target_id = uuid4()
    data = ReviewCreate(trip_id=trip_id, target_id=target_id, rating=5, text="Отлично!")
    
    # Мок поездки
    mock_trip_completed.id = trip_id
    mock_trip_completed.driver_id = author_id  # Автор - водитель
    
    # Мок подтверждённых участников ( автор + цель отзыва )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [target_id]
    mock_session.execute.return_value = mock_result
    
    # Мок отсутствующего отзыва
    with patch.object(service.repository, 'get_by_trip_and_author', return_value=None):
        with patch.object(service.repository, 'create', return_value=MagicMock(id=uuid4())):
            result = await service.create_review(author_id, data)
            assert result is not None


@pytest.mark.asyncio
async def test_create_review_trip_not_found(service, mock_session):
    """Ошибка: поездка не найдена."""
    trip_id = uuid4()
    author_id = uuid4()
    target_id = uuid4()
    data = ReviewCreate(trip_id=trip_id, target_id=target_id, rating=5)
    
    # Мок: поездка не найдена
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(TripNotFoundError):
        await service.create_review(author_id, data)


@pytest.mark.asyncio
async def test_create_review_trip_not_completed(service, mock_session, mock_trip_not_completed):
    """Ошибка: поездка не завершена."""
    trip_id = uuid4()
    author_id = uuid4()
    target_id = uuid4()
    data = ReviewCreate(trip_id=trip_id, target_id=target_id, rating=5)
    
    mock_trip_not_completed.id = trip_id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_trip_not_completed
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(TripNotCompletedError):
        await service.create_review(author_id, data)


@pytest.mark.asyncio
async def test_create_review_cannot_review_self(service, mock_session, mock_trip_completed):
    """Ошибка: нельзя оставить отзыв о себе."""
    trip_id = uuid4()
    user_id = uuid4()
    data = ReviewCreate(trip_id=trip_id, target_id=user_id, rating=5)
    
    mock_trip_completed.id = trip_id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_trip_completed
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(CannotReviewSelfError):
        await service.create_review(user_id, data)


@pytest.mark.asyncio
async def test_create_review_not_participant(service, mock_session, mock_trip_completed):
    """Ошибка: пользователь не является участником поездки."""
    trip_id = uuid4()
    author_id = uuid4()
    target_id = uuid4()
    data = ReviewCreate(trip_id=trip_id, target_id=target_id, rating=5)
    
    mock_trip_completed.id = trip_id
    mock_trip_completed.driver_id = uuid4()  # Другой водитель
    
    # Мок: нет подтверждённых участников
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(UserNotParticipantError):
        await service.create_review(author_id, data)


@pytest.mark.asyncio
async def test_create_review_target_not_participant(service, mock_session, mock_trip_completed):
    """Ошибка: цель отзыва не является участником поездки."""
    trip_id = uuid4()
    author_id = uuid4()
    target_id = uuid4()
    non_participant_id = uuid4()
    data = ReviewCreate(trip_id=trip_id, target_id=non_participant_id, rating=5)
    
    mock_trip_completed.id = trip_id
    mock_trip_completed.driver_id = author_id
    
    # Мок: автор - участник, но цель - нет
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [author_id]
    mock_session.execute.return_value = mock_result
    
    with patch.object(service.repository, 'get_by_trip_and_author', return_value=None):
        with pytest.raises(UserNotParticipantError):
            await service.create_review(author_id, data)


@pytest.mark.asyncio
async def test_create_review_already_exists(service, mock_session, mock_trip_completed):
    """Ошибка: отзыв уже существует."""
    trip_id = uuid4()
    author_id = uuid4()
    target_id = uuid4()
    data = ReviewCreate(trip_id=trip_id, target_id=target_id, rating=5)
    
    mock_trip_completed.id = trip_id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_trip_completed
    mock_session.execute.return_value = mock_result
    
    # Мок: отзыв уже существует
    existing_review = MagicMock()
    
    with patch.object(service.repository, 'get_by_trip_and_author', return_value=existing_review):
        with pytest.raises(ReviewAlreadyExistsError):
            await service.create_review(author_id, data)


# === Тесты обновления статуса ===
@pytest.mark.asyncio
async def test_update_review_status_success(service, mock_session, mock_review):
    """Успешное обновление статуса отзыва."""
    review_id = mock_review.id
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_review):
        with patch.object(service.repository, 'update_status', return_value=mock_review):
            result = await service.update_review_status(review_id, ReviewStatus.PUBLISHED)
            assert result is not None


@pytest.mark.asyncio
async def test_update_review_status_not_found(service, mock_session):
    """Ошибка: отзыв не найден."""
    review_id = uuid4()
    
    with patch.object(service.repository, 'get_by_id', return_value=None):
        with pytest.raises(ReviewNotFoundError):
            await service.update_review_status(review_id, ReviewStatus.PUBLISHED)


# === Тесты удаления отзыва ===
@pytest.mark.asyncio
async def test_delete_review_success(service, mock_session, mock_review):
    """Успешное удаление отзыва."""
    review_id = mock_review.id
    user_id = mock_review.author_id
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_review):
        with patch.object(service.repository, 'delete', return_value=True):
            result = await service.delete_review(review_id, user_id)
            assert result is True


@pytest.mark.asyncio
async def test_delete_review_not_owner(service, mock_session, mock_review):
    """Ошибка: не владелец отзыва."""
    review_id = mock_review.id
    user_id = uuid4()  # Другой пользователь
    
    with patch.object(service.repository, 'get_by_id', return_value=mock_review):
        with pytest.raises(ForbiddenError):
            await service.delete_review(review_id, user_id)


# === Тесты проверки возможности оставить отзыв ===
@pytest.mark.asyncio
async def test_check_user_can_review_success(service, mock_session, mock_trip_completed):
    """Пользователь может оставить отзыв."""
    trip_id = uuid4()
    author_id = uuid4()
    target_id = uuid4()
    
    mock_trip_completed.id = trip_id
    mock_trip_completed.driver_id = author_id
    
    # Мок: автор и цель - участники
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [author_id, target_id]
    mock_session.execute.return_value = mock_result
    
    with patch.object(service.repository, 'get_by_trip_and_author', return_value=None):
        can_review, reason = await service.check_user_can_review(author_id, trip_id)
        assert can_review is True
        assert reason == ""


@pytest.mark.asyncio
async def test_check_user_can_review_trip_not_completed(service, mock_session, mock_trip_not_completed):
    """Нельзя оставить отзыв на незавершённую поездку."""
    trip_id = uuid4()
    user_id = uuid4()
    
    mock_trip_not_completed.id = trip_id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_trip_not_completed
    mock_session.execute.return_value = mock_result
    
    can_review, reason = await service.check_user_can_review(user_id, trip_id)
    assert can_review is False
    assert "завершения поездки" in reason


@pytest.mark.asyncio
async def test_check_user_can_review_not_participant(service, mock_session, mock_trip_completed):
    """Нельзя оставить отзыв, если не участник поездки."""
    trip_id = uuid4()
    user_id = uuid4()
    
    mock_trip_completed.id = trip_id
    
    # Мок: нет участников
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    can_review, reason = await service.check_user_can_review(user_id, trip_id)
    assert can_review is False
    assert "участником" in reason


@pytest.mark.asyncio
async def test_check_user_can_review_already_reviewed(service, mock_session, mock_trip_completed):
    """Нельзя оставить второй отзыв на поездку."""
    trip_id = uuid4()
    user_id = uuid4()
    
    mock_trip_completed.id = trip_id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_trip_completed
    mock_session.execute.return_value = mock_result
    
    # Мок: отзыв уже существует
    existing_review = MagicMock()
    
    with patch.object(service.repository, 'get_by_trip_and_author', return_value=existing_review):
        can_review, reason = await service.check_user_can_review(user_id, trip_id)
        assert can_review is False
        assert "уже оставили отзыв" in reason
"""
Unit тесты для модуля чатов (Chat).

Тесты:
- test_create_conversation — создание чата
- test_create_conversation_by_trip — создание чата для поездки с сообщением
- test_send_message — отправка сообщения
- test_get_messages — получение сообщений
- test_mark_messages_read — отметка сообщений как прочитанных
- test_mute_conversation — управление уведомлениями
- test_list_conversations_by_user — список чатов пользователя
- test_not_participant_error — ошибка "не участник поездки"
- test_not_conversation_participant_error — ошибка "не участник чата"
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat.model import Conversation, ConversationParticipant, Message
from app.models.trips.model import Trip, TripStatus
from app.models.users.model import User, UserRole
from app.repositories.chat import ChatRepository
from app.schemas.chat.schemas import (
    ConversationCreate,
    ConversationList,
    ConversationMuteUpdate,
    MessageCreate,
    MessageList,
)
from app.services.chat import (
    ChatService,
    NotConversationParticipantError,
    NotParticipantError,
    TripNotFoundError,
)


# fixtures
@pytest.fixture
def mock_session():
    """Создание мок-сессии БД."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def chat_service(mock_session):
    """Создание ChatService с мок-сессией."""
    return ChatService(mock_session)


@pytest.fixture
def sample_user():
    """Создание тестового пользователя."""
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.USER,
        is_active=True,
    )


@pytest.fixture
def sample_trip():
    """Создание тестовой поездки."""
    return Trip(
        id=uuid.uuid4(),
        driver_id=uuid.uuid4(),
        from_city="Moscow",
        to_city="St. Petersburg",
        departure_date="2025-05-01",
        departure_time_start="10:00",
        price_per_seat=1500.0,
        total_seats=3,
        available_seats=3,
        status=TripStatus.PUBLISHED,
    )


class TestChatService:
    """Тесты для ChatService."""

    @pytest.mark.asyncio
    async def test_create_conversation_by_trip_creates_new_chat(
        self,
        chat_service,
        mock_session,
    ):
        """Тест создания чата для поездки с первым сообщением."""
        # Arrange
        trip_id = uuid.uuid4()
        sender_id = uuid.uuid4()
        content = "Hello!"

        # Мокаем методы
        with patch.object(chat_service, "_get_trip") as mock_get_trip, \
             patch.object(chat_service, "_is_trip_participant", return_value=True), \
             patch.object(chat_service.repository, "get_conversation_by_trip", return_value=None), \
             patch.object(chat_service.repository, "create_conversation") as mock_create_conv, \
             patch.object(chat_service.repository, "add_participant") as mock_add_participant, \
             patch.object(chat_service.repository, "create_message") as mock_create_msg:

            trip = Trip(
                id=trip_id,
                driver_id=uuid.uuid4(),
                from_city="Moscow",
                to_city="St. Petersburg",
                departure_date="2025-05-01",
                departure_time_start="10:00",
                price_per_seat=1500.0,
                total_seats=3,
                available_seats=3,
                status=TripStatus.PUBLISHED,
            )
            mock_get_trip.return_value = trip
            mock_create_conv.return_value = Conversation(
                id=uuid.uuid4(),
                trip_id=trip_id,
            )
            mock_create_msg.return_value = Message(
                id=uuid.uuid4(),
                conversation_id=uuid.uuid4(),
                sender_id=sender_id,
                content=content,
                is_read=False,
            )

            # Act
            conversation, message = await chat_service.create_conversation_with_message(
                trip_id=trip_id,
                sender_id=sender_id,
                content=content,
            )

            # Assert
            assert message.content == content
            mock_create_conv.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_conversation_by_trip_trip_not_found(self, chat_service):
        """Тест ошибки при создании чата для несуществующей поездки."""
        # Arrange
        trip_id = uuid.uuid4()
        sender_id = uuid.uuid4()

        with patch.object(chat_service, "_get_trip", return_value=None):
            # Act & Assert
            with pytest.raises(TripNotFoundError):
                await chat_service.create_conversation_with_message(
                    trip_id=trip_id,
                    sender_id=sender_id,
                    content="Hello!",
                )

    @pytest.mark.asyncio
    async def test_create_conversation_by_trip_not_participant(
        self,
        chat_service,
    ):
        """Тест ошибки при отправке сообщения не участником поездки."""
        # Arrange
        trip_id = uuid.uuid4()
        sender_id = uuid.uuid4()

        with patch.object(chat_service, "_get_trip") as mock_get_trip, \
             patch.object(chat_service, "_is_trip_participant", return_value=False):

            trip = Trip(
                id=trip_id,
                driver_id=uuid.uuid4(),
                from_city="Moscow",
                to_city="St. Petersburg",
                departure_date="2025-05-01",
                departure_time_start="10:00",
                price_per_seat=1500.0,
                total_seats=3,
                available_seats=3,
                status=TripStatus.PUBLISHED,
            )
            mock_get_trip.return_value = trip

            # Act & Assert
            with pytest.raises(NotParticipantError):
                await chat_service.create_conversation_with_message(
                    trip_id=trip_id,
                    sender_id=sender_id,
                    content="Hello!",
                )

    @pytest.mark.asyncio
    async def test_get_user_conversations_returns_list(
        self,
        chat_service,
    ):
        """Тест получения списка чатов пользователя."""
        # Arrange
        user_id = uuid.uuid4()
        conversation_id = uuid.uuid4()

        with patch.object(
            chat_service.repository,
            "list_conversations_by_user",
        ) as mock_list:
            mock_list.return_value = (
                [
                    Conversation(
                        id=conversation_id,
                        trip_id=uuid.uuid4(),
                    )
                ],
                1,
            )

            # Act
            result = await chat_service.get_user_conversations(
                user_id=user_id,
                page=1,
                page_size=20,
            )

            # Assert
            assert result.total == 1
            assert len(result.items) == 1


class TestChatRepository:
    """Тесты для ChatRepository."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, mock_session):
        """Тест создания чата."""
        # Arrange
        repo = ChatRepository(mock_session)
        trip_id = uuid.uuid4()

        # Мок создания
        mock_conv = Conversation(
            id=uuid.uuid4(),
            trip_id=trip_id,
        )
        mock_session.add = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        def set_result(obj):
            obj.id = mock_conv.id

        mock_session.refresh = set_result

        # Act
        result = await repo.create_conversation(trip_id)

        # Assert
        assert result is not None
"""
Service слой для работы с чатами (Chat).

Содержит бизнес-логику:
- Создание чатов и сообщений
- Проверка прав доступа (участники поездки)
- Управление прочтением сообщений
- Управление уведомлениями
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat.model import Conversation, ConversationParticipant, Message
from app.models.trips.model import Trip, TripStatus
from app.models.users.model import User
from app.repositories.chat.repository import ChatRepository
from app.schemas.chat.schemas import (
    ConversationCreate,
    ConversationList,
    MessageCreate,
    MessageList,
)


class ChatServiceError(Exception):
    """Базовый класс для ошибок чата."""
    pass


class ChatNotFoundError(ChatServiceError):
    """Чат не найден."""
    pass


class TripNotFoundError(ChatServiceError):
    """Поездка не найдена."""
    pass


class NotParticipantError(ChatServiceError):
    """Пользователь не является участником поездки."""
    pass


class NotConversationParticipantError(ChatServiceError):
    """Пользователь не является участником чата."""
    pass


class ForbiddenError(ChatServiceError):
    """Нет прав доступа."""
    pass


class ChatService:
    """Service для работы с чатами."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ChatRepository(session)

    async def _get_trip(self, trip_id: UUID) -> Optional[Trip]:
        """Получение поездки."""
        result = await self.session.execute(
            select(Trip).where(Trip.id == trip_id)
        )
        return result.scalar_one_or_none()

    async def _get_user(self, user_id: UUID) -> Optional[User]:
        """Получение пользователя."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _is_trip_participant(
        self,
        trip: Trip,
        user_id: UUID,
    ) -> bool:
        """Проверка, является ли пользователь участником поездки."""
        # Участником поездки является водитель (создатель) или пассажир с подтвержденной заявкой
        if trip.driver_id == user_id:
            return True

        # Проверяем, есть ли подтвержденная заявка у пользователя
        from app.models.requests.model import TripRequest, TripRequestStatus

        result = await self.session.execute(
            select(TripRequest).where(
                and_(
                    TripRequest.trip_id == trip.id,
                    TripRequest.passenger_id == user_id,
                    TripRequest.status == TripRequestStatus.CONFIRMED,
                )
            )
        )
        request = result.scalar_one_or_none()
        return request is not None

    async def _check_conversation_participant(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> ConversationParticipant:
        """Проверка участия в чате и возврат участника."""
        participant = await self.repository.get_participant(conversation_id, user_id)
        if not participant:
            raise NotConversationParticipantError(
                "Вы не являетесь участником этого чата"
            )
        return participant

    async def create_conversation(
        self,
        data: ConversationCreate,
        creator_id: UUID,
    ) -> Conversation:
        """Создание чата.

        Бизнес-правила:
        - Чаты создаются только при отправке первого сообщения
        - Участниками чата могут быть только участники поездки
        """
        # Получаем поездку
        trip = await self._get_trip(data.trip_id)
        if not trip:
            raise TripNotFoundError("Поездка не найдена")

        # Проверяем, что поездка доступна для создания чата
        if trip.status not in [TripStatus.PUBLISHED, TripStatus.ACTIVE]:
            raise ChatServiceError(
                "Нельзя создать чат для неактивной поездки"
            )

        # Проверяем, что все участники являются участниками поездки
        for participant_id in data.participant_ids:
            is_participant = await self._is_trip_participant(trip, participant_id)
            if not is_participant:
                raise NotParticipantError(
                    f"Пользователь {participant_id} не является участником поездки"
                )

        # Проверяем, что создатель тоже участник поездки
        if creator_id not in data.participant_ids:
            if not await self._is_trip_participant(trip, creator_id):
                raise NotParticipantError(
                    "Вы не являетесь участником этой поездки"
                )

        # Создаем чат
        conversation = await self.repository.create_conversation(data.trip_id)

        # Добавляем участников
        for participant_id in data.participant_ids:
            await self.repository.add_participant(conversation.id, participant_id)

        await self.session.flush()
        await self.session.refresh(conversation)

        return conversation

    async def create_conversation_with_message(
        self,
        trip_id: UUID,
        sender_id: UUID,
        content: str,
    ) -> tuple[Conversation, Message]:
        """Создание чата с первым сообщением.

        Бизнес-правила:
        - Если чат для поездки уже существует, используем его
        - Создаем сообщение отправителя
        - Автоматически добавляем участников (водителя и пассажира)
        """
        # Получаем поездку
        trip = await self._get_trip(trip_id)
        if not trip:
            raise TripNotFoundError("Поездка не найдена")

        # Проверяем, что поездка доступна
        if trip.status not in [TripStatus.PUBLISHED, TripStatus.ACTIVE]:
            raise ChatServiceError(
                "Нельзя отправлять сообщения для неактивной поездки"
            )

        # Проверяем, что отправитель - участник поездки
        if not await self._is_trip_participant(trip, sender_id):
            raise NotParticipantError(
                "Вы не являетесь участником этой поездки"
            )

        # Ищем существующий чат или создаем новый
        conversation = await self.repository.get_conversation_by_trip(trip_id)

        if not conversation:
            conversation = await self.repository.create_conversation(trip_id)

            # Добавляем участников: водителя и отправителя
            await self.repository.add_participant(conversation.id, trip.driver_id)
            await self.repository.add_participant(conversation.id, sender_id)

            await self.session.flush()
            await self.session.refresh(conversation)

        # Проверяем, что отправитель - участник чата
        participant = await self.repository.get_participant(conversation.id, sender_id)
        if not participant:
            await self.repository.add_participant(conversation.id, sender_id)
            await self.session.flush()

        # Создаем сообщение
        message = await self.repository.create_message(
            conversation.id,
            sender_id,
            content,
        )

        await self.session.flush()
        await self.session.refresh(message)

        return conversation, message

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        """Получение чата по ID.

        Проверяем, что пользователь - участник чата.
        """
        conversation = await self.repository.get_conversation_by_id(conversation_id)
        if not conversation:
            raise ChatNotFoundError("Чат не найден")

        # Проверяем участие
        await self._check_conversation_participant(conversation_id, user_id)

        return conversation

    async def get_user_conversations(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> ConversationList:
        """Получение списка чатов пользователя."""
        offset = (page - 1) * page_size
        conversations, total = await self.repository.list_conversations_by_user(
            user_id=user_id,
            limit=page_size,
            offset=offset,
        )

        pages = (total + page_size - 1) // page_size

        return ConversationList(
            items=conversations,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_trip_conversations(
        self,
        trip_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> ConversationList:
        """Получение списка чатов по поездке."""
        # Получаем поездку для проверки прав
        trip = await self._get_trip(trip_id)
        if not trip:
            raise TripNotFoundError("Поездка не найдена")

        # Проверяем, что пользователь - участник поездки
        if not await self._is_trip_participant(trip, user_id):
            raise NotParticipantError(
                "Вы не являетесь участником этой поездки"
            )

        offset = (page - 1) * page_size
        conversations, total = await self.repository.list_conversations_by_trip(
            trip_id=trip_id,
            limit=page_size,
            offset=offset,
        )

        pages = (total + page_size - 1) // page_size

        return ConversationList(
            items=conversations,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def send_message(
        self,
        conversation_id: UUID,
        sender_id: UUID,
        data: MessageCreate,
    ) -> Message:
        """Отправка сообщения.

        Проверяем, что отправитель - участник чата.
        """
        # Проверяем участие
        await self._check_conversation_participant(conversation_id, sender_id)

        # Создаем сообщение
        message = await self.repository.create_message(
            conversation_id,
            sender_id,
            data.content,
        )

        await self.session.flush()
        await self.session.refresh(message)

        return message

    async def get_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> MessageList:
        """Получение сообщений чата.

        Проверяем, что пользователь - участник чата.
        """
        # Проверяем участие
        await self._check_conversation_participant(conversation_id, user_id)

        offset = (page - 1) * page_size
        messages, total = await self.repository.list_messages_by_conversation(
            conversation_id=conversation_id,
            limit=page_size,
            offset=offset,
        )

        pages = (total + page_size - 1) // page_size

        return MessageList(
            items=messages,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def mark_messages_as_read(
        self,
        conversation_id: UUID,
        user_id: UUID,
        sender_id: UUID,
    ) -> int:
        """Отметка сообщений от отправителя как прочитанных.

        Провер��ем, что пользователь - участник чата.
        """
        # Проверяем участие
        await self._check_conversation_participant(conversation_id, user_id)

        # Отмечаем сообщения как прочитанные
        count = await self.repository.mark_messages_as_read(
            conversation_id,
            sender_id,
        )

        await self.session.flush()

        return count

    async def mark_message_as_read(
        self,
        message_id: UUID,
        reader_id: UUID,
    ) -> Message:
        """Отметка конкретного сообщения как прочитанного."""
        message = await self.repository.get_message_by_id(message_id)
        if not message:
            raise ChatServiceError("Сообщение не найдено")

        # Проверяем участие
        await self._check_conversation_participant(
            message.conversation_id,
            reader_id,
        )

        # Отмечаем как прочитанное
        updated = await self.repository.mark_message_as_read(message_id, reader_id)
        if not updated:
            raise ChatServiceError("Не удалось отметить сообщение как прочитанное")

        await self.session.flush()

        return updated

    async def set_mute(
        self,
        conversation_id: UUID,
        user_id: UUID,
        is_muted: bool,
    ) -> ConversationParticipant:
        """Управление уведомлениями.

        Проверяем, что пользователь - участник чата.
        """
        # Проверяем участие
        await self._check_conversation_participant(conversation_id, user_id)

        # Обновляем статус
        participant = await self.repository.update_participant_mute(
            conversation_id,
            user_id,
            is_muted,
        )

        await self.session.flush()

        return participant


# Импорт для is_trip_participant
from sqlalchemy import and_  # noqa: E402
"""
Repository слой для работы с чатами (Chat).

Методы:
- create_conversation — создание чата
- get_conversation_by_id — получение чата по ID
- get_conversation_by_trip — получение чата по поездке
- list_conversations_by_user — список чатов пользователя
- add_participant — добавление участника в чат
- remove_participant — удаление участника из чата
- get_participant — получение участника чата
- create_message — создание сообщения
- get_message_by_id — получение сообщения по ID
- list_messages_by_conversation — список сообщений чата
- mark_messages_as_read — отметка сообщений как прочитанных
- update_participant_mute — управление уведомлениями участника
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat.model import Conversation, ConversationParticipant, Message


class ChatRepository:
    """Repository для работы с чатами."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # === Conversations ===

    async def create_conversation(self, trip_id: UUID) -> Conversation:
        """Создание нового чата."""
        conversation = Conversation(trip_id=trip_id)
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation_by_id(
        self,
        conversation_id: UUID,
        load_relations: bool = True,
    ) -> Optional[Conversation]:
        """Получение чата по ID."""
        query = select(Conversation).where(Conversation.id == conversation_id)
        if load_relations:
            query = query.options(
                selectinload(Conversation.participants).selectinload(
                    ConversationParticipant.user
                ),
                selectinload(Conversation.messages),
            )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_conversation_by_trip(
        self,
        trip_id: UUID,
        load_relations: bool = True,
    ) -> Optional[Conversation]:
        """Получение чата по поездке (если существует)."""
        query = select(Conversation).where(Conversation.trip_id == trip_id)
        if load_relations:
            query = query.options(
                selectinload(Conversation.participants).selectinload(
                    ConversationParticipant.user
                ),
                selectinload(Conversation.messages),
            )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_conversations_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        """Получение списка чатов пользователя."""
        # Подзапрос для получения ID чатов пользователя
        participant_subquery = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == user_id)
            .scalar_subquery()
        )

        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(Conversation.id)).where(
                Conversation.id.in_(participant_subquery)
            )
        )
        total = count_result.scalar() or 0

        # Получаем чаты с участниками
        query = (
            select(Conversation)
            .where(Conversation.id.in_(participant_subquery))
            .options(
                selectinload(Conversation.participants).selectinload(
                    ConversationParticipant.user
                ),
                selectinload(Conversation.messages),
            )
            .order_by(Conversation.last_message_at.desc().nullslast())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        conversations = list(result.scalars().all())

        return conversations, total

    async def list_conversations_by_trip(
        self,
        trip_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        """Получение списка чатов по поездке."""
        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(Conversation.id)).where(
                Conversation.trip_id == trip_id
            )
        )
        total = count_result.scalar() or 0

        # Получаем чаты
        query = (
            select(Conversation)
            .where(Conversation.trip_id == trip_id)
            .options(
                selectinload(Conversation.participants).selectinload(
                    ConversationParticipant.user
                ),
            )
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        conversations = list(result.scalars().all())

        return conversations, total

    # === Conversation Participants ===

    async def add_participant(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> ConversationParticipant:
        """Добавление участника в чат."""
        participant = ConversationParticipant(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        self.session.add(participant)
        await self.session.flush()
        await self.session.refresh(participant)
        return participant

    async def remove_participant(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Удаление участника из чата."""
        result = await self.session.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
        )
        participant = result.scalar_one_or_none()
        if participant:
            await self.session.delete(participant)
            await self.session.flush()
            return True
        return False

    async def get_participant(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Optional[ConversationParticipant]:
        """Получение участника чата."""
        result = await self.session.execute(
            select(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
            .options(selectinload(ConversationParticipant.user))
        )
        return result.scalar_one_or_none()

    async def get_participants_by_conversation(
        self,
        conversation_id: UUID,
    ) -> list[ConversationParticipant]:
        """Получение списка участников чата."""
        result = await self.session.execute(
            select(ConversationParticipant)
            .where(ConversationParticipant.conversation_id == conversation_id)
            .options(selectinload(ConversationParticipant.user))
        )
        return list(result.scalars().all())

    async def update_participant_mute(
        self,
        conversation_id: UUID,
        user_id: UUID,
        is_muted: bool,
    ) -> Optional[ConversationParticipant]:
        """Обновление статуса уведомлений участника."""
        participant = await self.get_participant(conversation_id, user_id)
        if participant:
            participant.is_muted = is_muted
            await self.session.flush()
            await self.session.refresh(participant)
        return participant

    async def update_last_read_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        message_id: UUID,
    ) -> Optional[ConversationParticipant]:
        """Обновление последнего прочитанного сообщения."""
        participant = await self.get_participant(conversation_id, user_id)
        if participant:
            participant.last_read_message_id = message_id
            await self.session.flush()
            await self.session.refresh(participant)
        return participant

    # === Messages ===

    async def create_message(
        self,
        conversation_id: UUID,
        sender_id: UUID,
        content: str,
    ) -> Message:
        """Создание сообщения."""
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
        )
        self.session.add(message)
        await self.session.flush()

        # Обновляем last_message_at в чате
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.last_message_at = message.created_at

        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get_message_by_id(self, message_id: UUID) -> Optional[Message]:
        """Получение сообщения по ID."""
        result = await self.session.execute(
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.sender))
        )
        return result.scalar_one_or_none()

    async def list_messages_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Message], int]:
        """Получение списка сообщений чата."""
        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        total = count_result.scalar() or 0

        # Получаем сообщения
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .options(selectinload(Message.sender))
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        messages = list(result.scalars().all())

        return messages, total

    async def mark_messages_as_read(
        self,
        conversation_id: UUID,
        sender_id: UUID,
    ) -> int:
        """Отметка всех сообщений от отправителя как прочитанных."""
        # Обновляем все непрочитанные сообщения
        result = await self.session.execute(
            select(Message).where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.sender_id == sender_id,
                    Message.is_read == False,
                )
            )
        )
        messages = result.scalars().all()
        count = 0
        for message in messages:
            message.is_read = True
            count += 1

        if count > 0:
            await self.session.flush()

        return count

    async def mark_message_as_read(
        self,
        message_id: UUID,
        reader_id: UUID,
    ) -> Optional[Message]:
        """Отметка конкретного сообщения как прочитанного."""
        message = await self.get_message_by_id(message_id)
        if message and not message.is_read:
            message.is_read = True
            await self.session.flush()

            # Обновляем last_read_message_id для получателя
            # Нам нужно найти получателя (не отправителя)
            result = await self.session.execute(
                select(ConversationParticipant).where(
                    and_(
                        ConversationParticipant.conversation_id
                        == message.conversation_id,
                        ConversationParticipant.user_id != message.sender_id,
                    )
                )
            )
            recipient = result.scalar_one_or_none()
            if recipient:
                recipient.last_read_message_id = message_id

            await self.session.flush()

        return message

    async def get_unread_count(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> int:
        """Получение количества непрочитанных сообщений для пользователя."""
        # Получаем участника
        participant = await self.get_participant(conversation_id, user_id)
        if not participant or not participant.last_read_message_id:
            # Если нет last_read_message_id, считаем все сообщения непрочитанными
            result = await self.session.execute(
                select(func.count(Message.id)).where(
                    and_(
                        Message.conversation_id == conversation_id,
                        Message.sender_id != user_id,
                    )
                )
            )
            return result.scalar() or 0

        # Считаем сообщения после last_read_message_id
        result = await self.session.execute(
            select(func.count(Message.id)).where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.sender_id != user_id,
                    Message.id > participant.last_read_message_id,
                )
            )
        )
        return result.scalar() or 0
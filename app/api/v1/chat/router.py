"""
Роутер домена Chat.

Эндпоинты:
- POST /conversations — создание чата
- GET /conversations — список чатов пользователя
- GET /conversations/{conversation_id} — получение чата
- GET /conversations/{conversation_id}/messages — получение сообщений
- POST /conversations/{conversation_id}/messages — отправка сообщения
- PUT /conversations/{conversation_id}/read — отметка о прочтении
- PUT /conversations/{conversation_id}/mute — управление уведомлениями
- POST /conversations/by-trip — создание чата для поездки с первым сообщением

WebSocket: app/api/websocket.py
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.api.deps import get_db_session, get_current_user
from app.models.users.model import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationCreateResponse,
    ConversationList,
    ConversationMuteUpdate,
    MessageCreate,
    MessageCreateResponse,
    MessageList,
    MessageRead,
)
from app.services.chat import (
    ChatService,
    ChatServiceError,
    ChatNotFoundError,
    NotConversationParticipantError,
    NotParticipantError,
    TripNotFoundError,
)
from app.db.session import AsyncSession

router = APIRouter()
security = HTTPBearer()


async def get_current_user_dep(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Получение текущего пользователя из токена."""
    return await get_current_user(credentials.credentials)


async def get_chat_service(
    session: AsyncSession = Depends(get_db_session),
) -> ChatService:
    """Получение сервиса чатов."""
    return ChatService(session)


@router.post(
    "/conversations/by-trip",
    response_model=ConversationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание чата для поездки с первым сообщением",
    description="Создает чат для поездки (если его нет) и отправляет первое сообщение. "
    "Автоматически добавляет водителя и отправителя как участников.",
)
async def create_conversation_by_trip(
    trip_id: UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user_dep),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationCreateResponse:
    """Создание чата для поездки с первым сообщением."""
    try:
        conversation, message = await chat_service.create_conversation_with_message(
            trip_id=trip_id,
            sender_id=current_user.id,
            content=data.content,
        )
        await chat_service.session.commit()
        return ConversationCreateResponse(
            id=conversation.id,
            trip_id=conversation.trip_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            last_message_at=conversation.last_message_at,
            participants=[],  # Загружается отдельно при необходимости
            last_message=MessageCreateResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                sender_id=message.sender_id,
                content=message.content,
                is_read=message.is_read,
                created_at=message.created_at,
                updated_at=message.updated_at,
            ),
        )
    except TripNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Поездка не найдена",
        )
    except NotParticipantError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этой поездки",
        )
    except ChatServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/conversations",
    response_model=ConversationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание чата",
    description="Создает новый чат. Все участники должны быть участниками поездки.",
)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user_dep),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationCreateResponse:
    """Создание чата."""
    try:
        conversation = await chat_service.create_conversation(
            data=data,
            creator_id=current_user.id,
        )
        await chat_service.session.commit()
        return ConversationCreateResponse.model_validate(conversation)
    except TripNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Поездка не найдена",
        )
    except NotParticipantError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ChatServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/conversations",
    response_model=ConversationList,
    summary="Список чатов пользователя",
    description="Возвращает список всех чатов, в которых участвует пользователь.",
)
async def list_conversations(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    current_user: User = Depends(get_current_user_dep),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationList:
    """Получение списка чатов пользователя."""
    return await chat_service.get_user_conversations(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/conversations/trip/{trip_id}",
    response_model=ConversationList,
    summary="Список чатов по поездке",
    description="Возвращает список чатов для конкретной поездки. "
    "Доступно только участникам поездки.",
)
async def list_conversations_by_trip(
    trip_id: UUID,
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    current_user: User = Depends(get_current_user_dep),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationList:
    """Получение списка чатов по поездке."""
    try:
        return await chat_service.get_trip_conversations(
            trip_id=trip_id,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
        )
    except TripNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Поездка не найдена",
        )
    except NotParticipantError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этой поездки",
        )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationCreateResponse,
    summary="Получение чата",
    description="Возвращает информацию о чате. Доступно только участникам.",
)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationCreateResponse:
    """Получение чата по ID."""
    try:
        conversation = await chat_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
        return ConversationCreateResponse.model_validate(conversation)
    except ChatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    except NotConversationParticipantError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этого чата",
        )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageList,
    summary="Получение сообщений чата",
    description="Возвращает список сообщений в чате. "
    "Доступно только участникам чата.",
)
async def get_messages(
    conversation_id: UUID,
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=100, description="Размер страницы"),
    current_user: User = Depends(get_current_user_dep),
    chat_service: ChatService = Depends(get_chat_service),
) -> MessageList:
    """Получение сообщений чата."""
    try:
        return await chat_service.get_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
        )
    except ChatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    except NotConversationParticipantError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этого чата",
        )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Отправка сообщения",
    description="Отправляет сообщение в чат. "
    "Доступно только участникам чата.",
)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user_dep),
    chat_service: ChatService = Depends(get_chat_service),
) -> MessageCreateResponse:
    """Отправка сообщения в чат."""
    try:
        message = await chat_service.send_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            data=data,
        )
        await chat_service.session.commit()
        return MessageCreateResponse.model_validate(message)
    except ChatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    except NotConversationParticipantError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этого чата",
        )


@router.post(
    "/conversations/{conversation_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отметка сообщений как прочитанных",
    description="Отмечает все сообщения от указанного отправителя как прочитанные.",
)
async def mark_messages_read(
    conversation_id: UUID,
    data: MessageRead,
    current_user: User = Depends(get_current_user_dep),
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    """Отметка сообщений как прочитанных."""
    try:
        await chat_service.mark_messages_as_read(
            conversation_id=conversation_id,
            user_id=current_user.id,
            sender_id=data.message_id,
        )
        await chat_service.session.commit()
    except ChatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    except NotConversationParticipantError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этого чата",
        )


@router.put(
    "/conversations/{conversation_id}/mute",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Управление уведомлениями",
    description="Включает или отключает уве��омления для чата.",
)
async def set_mute(
    conversation_id: UUID,
    data: ConversationMuteUpdate,
    current_user: User = Depends(get_current_user_dep),
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    """Управление уведомлениями."""
    try:
        await chat_service.set_mute(
            conversation_id=conversation_id,
            user_id=current_user.id,
            is_muted=data.is_muted,
        )
        await chat_service.session.commit()
    except ChatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )
    except NotConversationParticipantError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этого чата",
        )
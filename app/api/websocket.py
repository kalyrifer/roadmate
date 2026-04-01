"""
WebSocket роутер для чата.
"""
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Менеджер WebSocket соединений."""

    def __init__(self) -> None:
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Подключение пользователя."""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        """Отключение пользователя."""
        self.active_connections.pop(user_id, None)

    async def send_personal_message(self, message: Any, user_id: int) -> None:
        """Отправка сообщения конкретному пользователю."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, message: Any) -> None:
        """Широковещательная рассылка."""
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:
    """
    WebSocket эндпоинт для real-time чата.
    
    HTTP Fallback: если WebSocket недоступен,
    используйте REST API эндпоинты для polling.
    """
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Обработка входящих сообщений
            await manager.send_personal_message(
                {"status": "received", "data": data},
                user_id,
            )
    except WebSocketDisconnect:
        manager.disconnect(user_id)
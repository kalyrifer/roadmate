"""
Тесты для базовой архитектуры.
"""
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Фикстура для тестового клиента."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Тест корневого эндпоинта."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "RoadMate"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Тест проверки здоровья."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
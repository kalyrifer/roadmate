"""
Роутер домена Auth.
Эндпоинты:
- POST /register — регистрация
- POST /login — вход
- POST /logout — выход
- GET /me — текущий пользователь
- POST /refresh — обновление токена
- POST /password-reset — сброс пароля
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register() -> dict[str, str]:
    """Регистрация нового пользователя."""
    return {"message": "Register endpoint"}


@router.post("/login")
async def login() -> dict[str, str]:
    """Вход в систему."""
    return {"message": "Login endpoint"}


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Выход из системы."""
    return {"message": "Logout endpoint"}


@router.get("/me")
async def get_current_user() -> dict[str, str]:
    """Получение текущего пользователя."""
    return {"message": "Current user endpoint"}


@router.post("/refresh")
async def refresh_token() -> dict[str, str]:
    """Обновление access токена."""
    return {"message": "Refresh token endpoint"}


@router.post("/password-reset")
async def reset_password() -> dict[str, str]:
    """Запрос на сброс пароля."""
    return {"message": "Password reset endpoint"}
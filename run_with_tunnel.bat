@echo off
chcp 65001 >nul
echo ========================================
echo   ЗАПУСК ROADMATE C ТУННЕЛЕМ
echo ========================================
echo.
echo Инструкция:
echo 1. Этот скрипт запустит сервер и туннель
echo 2. Дождитесь появления URL (строка начинается с https://)
echo 3. Скопируйте URL и отправьте другу
echo.
echo ВНИМАНИЕ: Не закрывайте это окно пока тестируете!
echo.
echo ========================================
echo.

echo [1/2] Запуск сервера (окно откроется отдельно)...
start /D D:\RoadMate\app python -m uvicorn main:app --host 0.0.0.0 --port 8000

echo.
echo [2/2] Запуск туннеля...
echo.
D:\RoadMate\cloudflared.exe tunnel --url localhost:8000

pause
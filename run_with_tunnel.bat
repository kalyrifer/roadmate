@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ========================================
echo   ROADMATE: BACKEND + FRONTEND + TUNNEL
echo ========================================
echo.
echo Корень проекта: %ROOT%
echo.

set "PY=%ROOT%\.venv\Scripts\python.exe"
set "CF=%ROOT%\cloudflared.exe"
set "FRONT=%ROOT%\frontend"

if not exist "%PY%" (
    echo [ОШИБКА] Не найден Python venv: %PY%
    echo Создай виртуальное окружение и установи зависимости backend:
    echo     cd /d "%ROOT%"
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "%CF%" (
    echo [ОШИБКА] Не найден cloudflared.exe: %CF%
    echo Скачай с https://github.com/cloudflare/cloudflared/releases/latest
    echo и положи cloudflared.exe в корень проекта.
    echo.
    pause
    exit /b 1
)

if not exist "%FRONT%\package.json" (
    echo [ОШИБКА] Не найден frontend\package.json
    pause
    exit /b 1
)

if not exist "%FRONT%\node_modules\react-day-picker" (
    echo [инфо] Устанавливаю зависимости frontend (npm install)...
    pushd "%FRONT%"
    call npm install
    if errorlevel 1 (
        echo [ОШИБКА] npm install завершился с ошибкой.
        popd
        pause
        exit /b 1
    )
    popd
)

echo [1/3] Запускаю backend (FastAPI, порт 8000) в отдельном окне...
start "RoadMate Backend" /D "%ROOT%" cmd /k ""%PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [2/3] Запускаю frontend (Vite, порт 5173) в отдельном окне...
start "RoadMate Frontend" /D "%FRONT%" cmd /k "npm run dev"

echo.
echo Жду готовности frontend на http://localhost:5173 ...
set /a WAIT=0
:waitloop
set /a WAIT+=1
if !WAIT! GTR 60 (
    echo [ОШИБКА] Frontend не поднялся за 60 секунд. Проверь окно "RoadMate Frontend".
    pause
    exit /b 1
)
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://localhost:5173 -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto waitloop
)
echo Frontend готов.
echo.

echo [3/3] Поднимаю туннель Cloudflare на http://localhost:5173 ...
echo.
echo Дождись строки вида https://xxxxx.trycloudflare.com
echo Это и есть публичный URL для друга.
echo Не закрывай это окно — пока оно открыто, туннель работает.
echo.

"%CF%" tunnel --url http://localhost:5173

echo.
echo Туннель остановлен.
pause
endlocal

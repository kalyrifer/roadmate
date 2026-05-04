@echo off
chcp 65001 >nul 2>&1
title RoadMate Tunnel

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "PY=%ROOT%\.venv\Scripts\python.exe"
set "CF=%ROOT%\cloudflared.exe"
set "FRONT=%ROOT%\frontend"
set "TUNNEL_RUNNER=%ROOT%\scripts\share_tunnel.py"

echo ========================================
echo   ROADMATE: BACKEND + FRONTEND + TUNNEL
echo ========================================
echo.
echo Project root: %ROOT%
echo.

if not exist "%PY%" goto no_venv
if not exist "%CF%" goto no_cf
if not exist "%FRONT%\package.json" goto no_front
if not exist "%TUNNEL_RUNNER%" goto no_runner
if not exist "%FRONT%\node_modules\react-day-picker" goto npm_install
goto run

:no_venv
echo [ERROR] Python venv not found: %PY%
echo Create venv and install backend deps:
echo     cd /d "%ROOT%"
echo     python -m venv .venv
echo     .venv\Scripts\pip install -r requirements.txt
echo.
pause
exit /b 1

:no_cf
echo [ERROR] cloudflared.exe not found: %CF%
echo Download from https://github.com/cloudflare/cloudflared/releases/latest
echo and place cloudflared.exe at the project root.
echo.
pause
exit /b 1

:no_front
echo [ERROR] frontend\package.json not found
echo.
pause
exit /b 1

:no_runner
echo [ERROR] tunnel runner not found: %TUNNEL_RUNNER%
echo Make sure the repo is up to date (git pull) — scripts\share_tunnel.py is required.
echo.
pause
exit /b 1

:npm_install
echo [info] Installing frontend deps (npm install)...
pushd "%FRONT%"
call npm install
if errorlevel 1 (
    popd
    echo [ERROR] npm install failed.
    pause
    exit /b 1
)
popd

:run
echo [1/4] Starting backend (FastAPI on port 8000) in a new window...
start "RoadMate Backend" /D "%ROOT%" cmd /k "%PY% -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [2/4] Starting frontend (Vite on port 5173) in a new window...
start "RoadMate Frontend" /D "%FRONT%" cmd /k "npm run dev"

echo.
echo Waiting for backend at http://localhost:8000/docs ...
set WAIT=0
:wait_backend
set /a WAIT=WAIT+1
if %WAIT% GTR 60 goto wait_backend_fail
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://localhost:8000/docs -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_backend
)
echo Backend is up.
echo.

echo Waiting for frontend at http://localhost:5173 ...
set WAIT=0
:wait_frontend
set /a WAIT=WAIT+1
if %WAIT% GTR 60 goto wait_frontend_fail
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://localhost:5173 -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_frontend
)
echo Frontend is up.
echo.
goto tunnel

:wait_backend_fail
echo [ERROR] Backend did not start within 60 seconds on port 8000.
echo Check the "RoadMate Backend" window for errors (DB connection, port in use, etc.).
pause
exit /b 1

:wait_frontend_fail
echo [ERROR] Frontend did not start within 60 seconds on port 5173.
echo Check the "RoadMate Frontend" window for errors.
pause
exit /b 1

:tunnel
echo [3/4] Starting Cloudflare tunnel for http://localhost:5173 ...
echo [4/4] Public URL will be printed in a banner below — copy and share it.
echo.

"%PY%" "%TUNNEL_RUNNER%"

echo.
echo Tunnel stopped.
pause

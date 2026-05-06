@echo off
chcp 65001 >nul 2>&1
title RoadMate Tunnel
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "PY=%ROOT%\.venv\Scripts\python.exe"
set "CF=%ROOT%\cloudflared.exe"
set "FRONT=%ROOT%\frontend"
set "TUNNEL_RUNNER=%ROOT%\scripts\share_tunnel.py"
set "RUN_LOGGED=%ROOT%\scripts\run_logged.ps1"
set "LOG_DIR=%ROOT%\logs"
set "BACKEND_LOG=%LOG_DIR%\backend.log"
set "FRONTEND_LOG=%LOG_DIR%\frontend.log"

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
if not exist "%RUN_LOGGED%" goto no_runner
if not exist "%FRONT%\node_modules\react-day-picker" goto npm_install
goto check_ports

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
echo [ERROR] helper script missing — make sure the repo is up to date (git pull).
echo Required: %TUNNEL_RUNNER%
echo Required: %RUN_LOGGED%
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

:check_ports
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

:: --- kill leftovers from previous runs so we always start clean -----------
echo [info] Cleaning up leftovers from previous runs (uvicorn, vite, cloudflared)...

call :kill_port 8000
call :kill_port 5173
call :kill_proc cloudflared.exe

:: stale tunnel URL files from previous runs would mislead the user — clear them
if exist "%LOG_DIR%\tunnel_url.txt" del /q "%LOG_DIR%\tunnel_url.txt" >nul 2>&1

:: short pause so the OS frees the sockets before we try to bind again
ping -n 2 127.0.0.1 >nul 2>&1

:: re-check; if a port is *still* busy we genuinely cannot continue
call :port_in_use 8000
if "%PORT_BUSY%"=="1" (
    echo [ERROR] Port 8000 is still in use after cleanup:
    netstat -ano | findstr ":8000" | findstr "LISTENING"
    echo Close the process holding port 8000 manually, then retry.
    echo.
    pause
    exit /b 1
)

call :port_in_use 5173
if "%PORT_BUSY%"=="1" (
    echo [ERROR] Port 5173 is still in use after cleanup:
    netstat -ano | findstr ":5173" | findstr "LISTENING"
    echo Close the process holding port 5173 manually, then retry.
    echo.
    pause
    exit /b 1
)
echo [info] Cleanup done.
echo.

:run
echo [1/4] Starting backend (FastAPI on port 8000) in a new window...
echo       (live output also written to %BACKEND_LOG%)
start "RoadMate Backend" powershell -NoExit -NoProfile -ExecutionPolicy Bypass -File "%RUN_LOGGED%" -LogPath "%BACKEND_LOG%" -WorkDir "%ROOT%" "%PY%" "-m" "uvicorn" "app.main:app" "--host" "0.0.0.0" "--port" "8000"

echo [2/4] Starting frontend (Vite on port 5173) in a new window...
echo       (live output also written to %FRONTEND_LOG%)
start "RoadMate Frontend" powershell -NoExit -NoProfile -ExecutionPolicy Bypass -File "%RUN_LOGGED%" -LogPath "%FRONTEND_LOG%" -WorkDir "%FRONT%" "npm.cmd" "run" "dev"

echo.
echo Waiting for backend at http://127.0.0.1:8000/docs ...
set WAIT=0
:wait_backend
set /a WAIT=WAIT+1
if %WAIT% GTR 60 goto wait_backend_fail
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://127.0.0.1:8000/docs -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_backend
)
echo Backend is up.
echo.

echo Waiting for frontend at http://127.0.0.1:5173 ...
set WAIT=0
:wait_frontend
set /a WAIT=WAIT+1
if %WAIT% GTR 60 goto wait_frontend_fail
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://127.0.0.1:5173 -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_frontend
)
echo Frontend is up.
echo.
goto tunnel

:wait_backend_fail
echo.
echo [ERROR] Backend did not start within 60 seconds on port 8000.
echo.
echo ----- last lines of %BACKEND_LOG% -----
if exist "%BACKEND_LOG%" (
    powershell -NoProfile -Command "Get-Content -Path '%BACKEND_LOG%' -Tail 80"
) else (
    echo (log file not produced — RoadMate Backend window probably crashed before writing)
)
echo ----------------------------------------
echo.
echo Common causes:
echo   * PostgreSQL is not running on localhost:5432.
echo     Start it (Docker: docker compose up -d db) or check your .env DATABASE_URL.
echo   * Port 8000 is already used by an old uvicorn — close that window or run:
echo         netstat -ano ^| findstr ":8000"
echo   * Backend deps are missing or outdated — re-run:
echo         "%PY%" -m pip install -r "%ROOT%\requirements.txt"
echo.
pause
exit /b 1

:wait_frontend_fail
echo.
echo [ERROR] Frontend did not start within 60 seconds on port 5173.
echo.
echo ----- last lines of %FRONTEND_LOG% -----
if exist "%FRONTEND_LOG%" (
    powershell -NoProfile -Command "Get-Content -Path '%FRONTEND_LOG%' -Tail 80"
) else (
    echo (log file not produced — RoadMate Frontend window probably crashed before writing)
)
echo -----------------------------------------
echo.
pause
exit /b 1

:tunnel
echo [3/4] Starting Cloudflare tunnel for http://localhost:5173 ...
echo [4/4] Public URL will be printed in a banner below — copy and share it.
echo.

"%PY%" "%TUNNEL_RUNNER%"

echo.
echo ========================================================================
echo  Tunnel stopped.
echo  Any URL printed above (including the *.trycloudflare.com link) is now
echo  DEAD — Cloudflare quick-tunnels are gone the moment cloudflared exits.
echo  Run this script again to get a NEW public URL.
echo ========================================================================
pause
exit /b 0


:: --- helpers ----------------------------------------------------------------

:port_in_use
:: usage: call :port_in_use <port>
:: sets PORT_BUSY=1 if something is LISTENING on that port, else 0
set "PORT_BUSY=0"
for /f "tokens=*" %%L in ('netstat -ano ^| findstr ":%~1" ^| findstr "LISTENING" 2^>nul') do (
    set "PORT_BUSY=1"
)
exit /b 0

:kill_port
:: usage: call :kill_port <port>
:: kills every process LISTENING on the given TCP port
set "_KP_PORT=%~1"
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%_KP_PORT%" ^| findstr "LISTENING" 2^>nul') do (
    if not "%%P"=="0" (
        echo   [kill] port %_KP_PORT% — PID %%P
        taskkill /F /PID %%P >nul 2>&1
    )
)
exit /b 0

:kill_proc
:: usage: call :kill_proc <image-name.exe>
:: kills every process whose image name matches (e.g. cloudflared.exe)
set "_KN_NAME=%~1"
tasklist /FI "IMAGENAME eq %_KN_NAME%" 2>nul | findstr /I "%_KN_NAME%" >nul
if not errorlevel 1 (
    echo   [kill] %_KN_NAME%
    taskkill /F /IM "%_KN_NAME%" >nul 2>&1
)
exit /b 0

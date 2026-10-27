@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo  Starting VahanOne Transport Operating System
echo ==================================================

:: Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not installed or not in your system PATH.
    echo Please install Docker Desktop for Windows:
    echo https://docs.docker.com/desktop/setup/install/windows-install/
    exit /b 1
)

:: Check if Docker daemon is running
docker info >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker daemon is not running.
    echo Please launch Docker Desktop and wait until the engine is running, then re-run this script.
    exit /b 1
)

echo ==^> Docker is active. Building and launching services...
echo ==^> This spins up PostgreSQL, FastAPI backend (auto-migrated and seeded), and Vite frontend.
echo.

docker compose up --build -d
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to start Docker Compose services.
    exit /b %ERRORLEVEL%
)

echo.
echo ==================================================
echo  VahanOne is successfully running!
echo ==================================================
echo  Frontend Website : http://localhost
echo  Backend API Docs : http://localhost:8000/docs
echo  Backend Health   : http://localhost:8000/
echo.
echo  Default Demo Credentials:
echo    Email    : admin@vahanone.com
echo    Password : AdminPassword123!
echo    Org ID   : 00000000-0000-0000-0000-000000000001
echo.
echo  To view service logs:
echo    docker compose logs -f
echo.
echo  To stop all services:
echo    docker compose down
echo ==================================================
pause

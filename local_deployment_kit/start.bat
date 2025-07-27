@echo off
REM AI Crypto Trading Coach - Windows Quick Start Script

echo 🚀 AI Crypto Trading Coach - Local Deployment Setup
echo ==================================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Check if .env file exists
if not exist ".env" (
    echo ⚙️  Setting up environment configuration...
    if exist ".env.backend.example" (
        copy ".env.backend.example" ".env" >nul
        echo ✅ Environment template copied to .env
        echo ⚠️  IMPORTANT: Edit .env file and add your API keys before continuing!
        echo.
        echo Required API keys:
        echo   - LUNO_API_KEY ^(from https://www.luno.com/wallet/security/api_keys^)
        echo   - LUNO_SECRET
        echo   - GEMINI_API_KEY ^(from https://makersuite.google.com/app/apikey^)
        echo.
        set /p answer="Have you added your API keys to .env? (y/N): "
        if /i not "%answer%"=="y" (
            echo Please edit .env file first, then run this script again.
            pause
            exit /b 1
        )
    ) else (
        echo ❌ Error: .env.backend.example not found
        pause
        exit /b 1
    )
) else (
    echo ✅ Environment file exists
)

REM Check if frontend .env exists
if not exist "app\frontend\.env" (
    if exist ".env.frontend.example" (
        copy ".env.frontend.example" "app\frontend\.env" >nul
        echo ✅ Frontend environment configured
    )
)

REM Check if Freqtrade config exists
if not exist "app\freqtrade\config.json" (
    if exist "config.luno.example.json" (
        copy "config.luno.example.json" "app\freqtrade\config.json" >nul
        echo ✅ Freqtrade configuration set up
    )
)

echo.
echo 🐳 Starting AI Crypto Trading Coach services...
echo This may take a few minutes on first run...
echo.

REM Start the services
docker-compose up --build

echo.
echo 🎉 Setup complete! Your AI Crypto Trading Coach is running:
echo    Dashboard: http://localhost:3000
echo    Backend API: http://localhost:8001
echo.
echo To stop the services:
echo    Press Ctrl+C, then run: docker-compose down
pause
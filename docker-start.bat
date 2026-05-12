@echo off
REM SmartShrimp OpenClaw - Docker deployment

docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed.
    pause
    exit /b 1
)

if not exist data mkdir data
if not exist reports mkdir reports
if not exist logs mkdir logs

cd docker
docker compose build
if errorlevel 1 (
    docker-compose build
)

docker compose up -d
if errorlevel 1 (
    docker-compose up -d
)
cd ..

echo Dashboard: http://localhost:8501
pause

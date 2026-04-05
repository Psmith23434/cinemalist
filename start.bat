@echo off
title CinemaList Backend
cd /d "%~dp0backend"

echo.
echo  ==============================
echo   CinemaList - Starting server
echo  ==============================
echo.

call venv\Scripts\activate

echo  Applying any new database migrations...
alembic upgrade head

echo.
echo  Server starting at http://localhost:8000
echo  Swagger UI at   http://localhost:8000/docs
echo  Press Ctrl+C to stop.
echo.

uvicorn app.main:app --reload

pause

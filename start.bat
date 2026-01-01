@echo off
REM LLM Council - Start script for Windows

echo Starting LLM Council...
echo.

REM Start backend
echo Starting backend on http://localhost:8001...
start "LLM Council Backend" cmd /k python -m backend.main

REM Wait a bit for backend to start
timeout /t 2 /nobreak

REM Start frontend
echo Starting frontend on http://localhost:5173...
cd frontend
start "LLM Council Frontend" cmd /k npm run dev

echo.
echo LLM Council is starting!
echo   Backend:  http://localhost:8001
echo   Frontend: http://localhost:5173
echo.
echo Two new windows opened above. Close them individually or close this one to exit.
echo.
pause

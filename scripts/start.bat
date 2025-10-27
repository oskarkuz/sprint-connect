@echo off
echo Starting Sprint Connect...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Initialize database if it doesn't exist
if not exist "data\sprint_connect.db" (
    echo Initializing database with demo data...
    python -m backend.init_db
)

REM Start backend in new window
echo Starting backend API...
start "Sprint Connect Backend" cmd /k "venv\Scripts\activate && uvicorn backend.main:app --reload --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak

REM Start frontend
echo Starting frontend...
echo ----------------------------------------
echo Frontend will open at: http://localhost:8501
echo API docs available at: http://localhost:8000/docs
echo ----------------------------------------
echo Close this window to stop the frontend
echo Close the backend window to stop the API
echo ----------------------------------------

streamlit run frontend\app.py

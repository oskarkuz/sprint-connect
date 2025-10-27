@echo off
REM Setup script for Sprint Connect - Windows

echo ===================================
echo Sprint Connect Setup Script
echo ===================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Initialize database
echo.
echo Initializing database...
python -m backend.init_db

echo.
echo ===================================
echo Setup Complete!
echo ===================================
echo.
echo To start the application:
echo.
echo 1. Activate virtual environment:
echo    venv\Scripts\activate
echo.
echo 2. Start the backend (Terminal 1):
echo    uvicorn backend.main:app --reload --port 8000
echo.
echo 3. Start the frontend (Terminal 2):
echo    streamlit run frontend\app.py
echo.
echo Demo accounts:
echo   Student: sarah@srh.nl / demo123
echo   Admin: admin@srh.nl / admin123
echo.
pause

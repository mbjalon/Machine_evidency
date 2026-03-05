@echo off
cd /d "%~dp0"

echo Starting Machine Evidency...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Install / update requirements
echo Installing requirements...
venv\Scripts\pip install -r requirements.txt

REM Run the app
echo Starting application...
venv\Scripts\python run.py
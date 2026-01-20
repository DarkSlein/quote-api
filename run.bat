@echo off
cd %~dp0

if not exist "venv" (
    echo Virtual environment not found.
    echo Please run setup.py to create the virtual environment.
    pause
    exit /b
)

call venv/Scripts/activate

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
pause
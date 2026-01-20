@echo off
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and ensure it's in your PATH.
    pause
    exit /b
)

ping -n 1 www.google.com >nul 2>&1
if %errorlevel% neq 0 (
    echo No internet connection detected. Please connect to the internet and try again.
    pause
    exit /b
)

echo Installing virtual environment package...
python -m pip install virtualenv >nul 2>&1
if %errorlevel% neq 0 (
    echo Failed to install virtualenv. Please check your Python installation or internet connection.
    pause
    exit /b
)

echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment. Please check your Python installation.
    pause
    exit /b
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment. Please check your setup.
    pause
    exit /b
)

python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install required packages. Please check requirements.txt or internet connection.
    pause
    exit /b
)

echo Setup completed successfully.
pause
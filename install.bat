@echo off
echo ================================================
echo   Autonomous AI Task Worker - Installation
echo ================================================
echo.

REM Check Python
python --version
if errorlevel 1 (
    echo Error: Python not found
    exit /b 1
)

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Install Playwright
echo.
echo Installing Playwright browsers...
playwright install chromium

REM Create .env file
if not exist .env (
    echo.
    echo Creating .env file...
    copy .env.example .env
    echo WARNING: Please edit .env and add your ANTHROPIC_API_KEY
)

REM Create directories
if not exist task_states mkdir task_states

echo.
echo ================================================
echo   Installation Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Edit .env and add your ANTHROPIC_API_KEY
echo 2. Activate virtual environment:
echo    venv\Scripts\activate.bat
echo 3. Start the mock system:
echo    python demo\mock_system.py
echo 4. In another terminal, run the demo:
echo    python demo\run_demo.py
echo.
pause

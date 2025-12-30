@echo off
REM Automated setup script using uv for Windows
REM This script will install uv, Python, and all dependencies automatically

echo Starting automated setup with uv...
echo.

REM Check if uv is installed
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    REM Add uv to PATH for current session
    set PATH=%USERPROFILE%\.cargo\bin;%PATH%

    echo uv installed successfully
) else (
    echo uv is already installed
)

REM Create virtual environment with uv (will auto-install Python if needed)
echo Creating virtual environment with Python 3.11...
uv venv --python 3.11

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies using uv
echo Installing Python dependencies...
uv pip install -r requirements.txt

REM Install Playwright browsers
echo Installing Playwright Chromium browser...
python -m playwright install chromium

REM Create necessary directories
echo Creating required directories...
if not exist "output" mkdir output
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache
if not exist "backups" mkdir backups

REM Copy .env.example to .env if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file with your configuration
)

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To activate the environment:
echo   .venv\Scripts\activate.bat
echo.
echo To run the automation:
echo   python main.py "your-file.csv" --headless
echo.
pause

@echo off
REM Quick run script - automatically sets up environment if needed

REM Check if virtual environment exists
if not exist ".venv" (
    echo Virtual environment not found. Running setup...
    call setup.bat
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the automation with all arguments passed to this script
python main.py %*

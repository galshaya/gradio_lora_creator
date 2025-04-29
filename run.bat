@echo off
echo Starting LORA Trainer...

:: Check if pip is installed
where pip >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: pip is not installed. Please install Python and pip first.
    pause
    exit /b 1
)

:: Check if requirements are installed
echo Checking requirements...
set MISSING=0
pip freeze | findstr /i "opencv-python" >nul 2>nul || set MISSING=1
pip freeze | findstr /i "pillow" >nul 2>nul || set MISSING=1
pip freeze | findstr /i "gradio" >nul 2>nul || set MISSING=1
pip freeze | findstr /i "python-dotenv" >nul 2>nul || set MISSING=1
pip freeze | findstr /i "fal-client" >nul 2>nul || set MISSING=1
pip freeze | findstr /i "requests" >nul 2>nul || set MISSING=1
pip freeze | findstr /i "numpy" >nul 2>nul || set MISSING=1

:: Install requirements if needed
if %MISSING% equ 1 (
    echo Some requirements are missing. Installing now...
    pip install -r requirements.txt
) else (
    echo All requirements are installed.
)

:: Run the application
python lora_trainer.py
pause
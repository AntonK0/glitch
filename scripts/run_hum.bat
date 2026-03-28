@echo off
setlocal
cd /d "%~dp0.."
set AUDIO_PATH=%~1
if "%AUDIO_PATH%"=="" (
    echo Usage: run_hum.bat ^<audio_path^>
    exit /b 1
)
if "%PYTHON_314%"=="" set PYTHON_314=python
echo ^> Running hum-to-score agent...
"%PYTHON_314%" scripts/hum_launch.py "%AUDIO_PATH%"

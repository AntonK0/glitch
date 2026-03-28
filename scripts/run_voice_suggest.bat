@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0.."
set AUDIO_PATH=%~1
if "%AUDIO_PATH%"=="" (
    echo Usage: run_voice_suggest.bat ^<audio_path^>
    exit /b 1
)
if "%PYTHON_314%"=="" set PYTHON_314=python
echo ^> Transcribing voice...
for /f "delims=" %%i in ('"%PYTHON_314%" scripts/transcribe.py "%AUDIO_PATH%"') do set PROMPT=%%i
echo ^> You said: !PROMPT!
echo ^> Running composer agent...
"%PYTHON_314%" scripts/composer_launch.py "!PROMPT!"

@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0.."
set AUDIO_PATH=%~1
if "%AUDIO_PATH%"=="" (
    echo Usage: run_voice_demo.bat ^<audio_path^>
    exit /b 1
)
if "%PYTHON_314%"=="" set PYTHON_314=python
echo ^> Transcribing voice...
for /f "delims=" %%i in ('"%PYTHON_314%" scripts/transcribe.py "%AUDIO_PATH%"') do set PROMPT=%%i
echo ^> You said: !PROMPT!
echo ^> Running accompaniment agent...
"%PYTHON_314%" src/agents/accompany_agent.py "!PROMPT!"

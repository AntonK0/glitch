#!/usr/bin/env bash
# Voice → transcription → accompaniment agent (DEMO mode, generates Lyria WAV)
set -euo pipefail
cd "$(dirname "$0")/.."

AUDIO_PATH="${1:?Usage: run_voice_demo.sh <audio_path>}"
PYTHON="${PYTHON_314:-python3}"

echo "> Transcribing voice…"
PROMPT=$("$PYTHON" scripts/transcribe.py "$AUDIO_PATH")
echo "> You said: $PROMPT"

echo "> Running accompaniment agent…"
"$PYTHON" src/agents/accompany_agent.py "$PROMPT"

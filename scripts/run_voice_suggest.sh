#!/usr/bin/env bash
# Voice → transcription → MuseScore composer agent (SUGGEST mode)
set -euo pipefail
cd "$(dirname "$0")/.."

AUDIO_PATH="${1:?Usage: run_voice_suggest.sh <audio_path>}"
PYTHON="${PYTHON_314:-python3}"

echo "> Transcribing voice…"
PROMPT=$("$PYTHON" scripts/transcribe.py "$AUDIO_PATH")
echo "> You said: $PROMPT"

echo "> Running composer agent…"
"$PYTHON" scripts/composer_launch.py "$PROMPT"

#!/usr/bin/env bash
# Hum/melody recording → audio transcription + MuseScore write (dual-MCP)
set -euo pipefail
cd "$(dirname "$0")/.."

AUDIO_PATH="${1:?Usage: run_hum.sh <audio_path>}"
PYTHON="${PYTHON_314:-python3}"

echo "> Running hum-to-score agent…"
"$PYTHON" scripts/hum_launch.py "$AUDIO_PATH"

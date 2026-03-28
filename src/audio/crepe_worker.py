"""Standalone worker that runs CREPE transcription and prints result as JSON.

Invoked as a subprocess by audio_mcp_server.py to completely isolate
TensorFlow/CREPE from the MCP server process.
"""
import json
import os
import sys

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import warnings
warnings.filterwarnings("ignore")

import logging
logging.getLogger("tensorflow").setLevel(logging.ERROR)
logging.getLogger("keras").setLevel(logging.ERROR)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from crepe_parser import run_crepe_transcription


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: crepe_worker.py <audio_path> [confidence]"}))
        sys.exit(1)

    audio_path = sys.argv[1]
    confidence = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7

    if not os.path.exists(audio_path):
        print(json.dumps({"error": f"File {audio_path} not found."}))
        sys.exit(1)

    try:
        notes = run_crepe_transcription(audio_path, confidence_threshold=confidence)
        print(json.dumps({"notes": notes}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

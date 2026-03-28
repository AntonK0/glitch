#!/usr/bin/env python3
"""Transcribe a WAV file to text via Gemini. Prints transcription to stdout."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv

load_dotenv()


async def main():
    if len(sys.argv) < 2:
        print("Usage: transcribe.py <audio_path>", file=sys.stderr)
        sys.exit(1)

    audio_path = sys.argv[1]
    from google import genai
    from google.genai import types as gt

    client = genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    )
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    resp = await client.aio.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            gt.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
            "Transcribe exactly what the user said. Return only the transcription.",
        ],
    )
    print(resp.text.strip())


asyncio.run(main())

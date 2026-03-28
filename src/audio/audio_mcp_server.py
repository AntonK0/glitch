import json
import os
import subprocess
import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AudioProcessor")

WORKER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crepe_worker.py")


@mcp.tool()
async def transcribe_crepe(audio_path: str, confidence_threshold: float = 0.7) -> str:
    """Transcribe monophonic audio to MIDI note events using CREPE.

    Returns a list of tuples: (start_time, end_time, midi_pitch).
    """
    print(f"[AudioServer] transcribe_crepe called: {audio_path}", file=sys.stderr, flush=True)

    if not os.path.exists(audio_path):
        return f"Error: File {audio_path} not found."

    try:
        import anyio

        result = await anyio.to_thread.run_sync(
            lambda: _run_worker(audio_path, confidence_threshold)
        )
        return result
    except Exception as e:
        import traceback
        msg = f"Error during CREPE transcription: {e}\n{traceback.format_exc()}"
        print(f"[AudioServer] EXCEPTION: {msg}", file=sys.stderr, flush=True)
        return msg


def _run_worker(audio_path: str, confidence_threshold: float) -> str:
    """Spawn crepe_worker.py as a subprocess and return its result."""
    proc = subprocess.run(
        [sys.executable, WORKER_SCRIPT, audio_path, str(confidence_threshold)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=240,
    )

    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="", flush=True)

    if proc.returncode != 0:
        return f"Error: Worker exited with code {proc.returncode}. {proc.stderr}"

    try:
        data = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        return f"Error: Could not parse worker output: {proc.stdout[:200]}"

    if "error" in data:
        return f"Error: {data['error']}"

    notes = data.get("notes", [])
    print(f"[AudioServer] Done - {len(notes)} notes", file=sys.stderr, flush=True)

    if not notes:
        return (
            "No notes were detected in the audio file. "
            "The audio might be too quiet, or the confidence threshold too high."
        )
    return str(notes)


if __name__ == "__main__":
    print("[AudioServer] MCP server starting", file=sys.stderr, flush=True)
    mcp.run()

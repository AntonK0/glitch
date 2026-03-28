#!/usr/bin/env python3
"""Run the dual-MCP hum agent: audio transcription + MuseScore write."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
MUSESCORE_SERVER = str(PROJECT_ROOT / "mcp-musescore" / "server.py")
AUDIO_SERVER = str(PROJECT_ROOT / "src" / "audio" / "audio_mcp_server.py")
PYTHON_311 = os.environ.get("PYTHON_311", "python3.11")


async def main():
    if len(sys.argv) < 2:
        print("Usage: hum_launch.py <audio_path>", file=sys.stderr)
        sys.exit(1)

    audio_path = sys.argv[1]

    from google.adk.agents.llm_agent import Agent
    from google.adk.runners import InMemoryRunner
    from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
    from google.genai import types as gt
    from mcp import StdioServerParameters

    for label, path in [("MuseScore server", MUSESCORE_SERVER), ("Audio server", AUDIO_SERVER)]:
        if not os.path.exists(path):
            print(f"Error: {label} not found at {path}", file=sys.stderr)
            sys.exit(1)

    musescore_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable, args=[MUSESCORE_SERVER]
            ),
            timeout=30.0,
        )
    )
    audio_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=PYTHON_311, args=[AUDIO_SERVER]
            ),
            timeout=30.0,
        )
    )

    instruction = """
    You are a Senior Music Orchestrator and Transcription Expert.
    Process audio input into musical scores using BATCH operations.

    PIPELINE:
    1. TRANSCRIPTION: Use transcribe_crepe (monophonic/vocals) or transcribe_basic_pitch
       (polyphonic) on the provided audio file to extract notes.
    2. DISCOVERY: Call list_tracks once to identify available score tracks.
    3. ARCHITECTING: Map transcribed notes to measures. Verify rhythms match the time signature.
    4. ATOMIC EXECUTION: Use write_measures to write all notes in one call per instrument.

    CONSTRAINTS:
    - No granular note calls — batch everything.
    - Follow music theory.
    - If a track is missing, call create_track first.
    """

    agent = Agent(
        model="gemini-3-flash-preview",
        name="MuseScore_Hum_Architect",
        instruction=instruction,
        tools=[musescore_mcp, audio_mcp],
    )
    runner = InMemoryRunner(agent=agent, app_name="muse_hum")
    session = await runner.session_service.create_session(
        app_name="muse_hum", user_id="local_user"
    )
    content = gt.Content(
        role="user",
        parts=[gt.Part.from_text(
            text=f"Listen to {audio_path} and write it to the piano track."
        )],
    )

    print(f"--- Hum agent started | audio: {audio_path} ---")
    for event in runner.run(
        user_id="local_user", session_id=session.id, new_message=content
    ):
        if not event.content or not event.content.parts:
            continue
        for part in event.content.parts:
            if part.text and part.text.strip():
                print(part.text.strip(), flush=True)
            if part.function_call:
                print(f"[CALL: {part.function_call.name}]", flush=True)
            if part.function_response:
                print("[DONE]", flush=True)


asyncio.run(main())

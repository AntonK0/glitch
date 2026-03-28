#!/usr/bin/env python3
"""Run the MuseScore-only composer agent with a prompt from argv."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
MUSESCORE_SERVER = str(PROJECT_ROOT / "mcp-musescore" / "server.py")


async def main():
    user_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Write a melody"

    from google.adk.agents.llm_agent import Agent
    from google.adk.runners import InMemoryRunner
    from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
    from google.genai import types as gt
    from mcp import StdioServerParameters

    if not os.path.exists(MUSESCORE_SERVER):
        print(f"Error: MuseScore server not found at {MUSESCORE_SERVER}", file=sys.stderr)
        sys.exit(1)

    musescore_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable, args=[MUSESCORE_SERVER]
            ),
            timeout=30.0,
        )
    )

    instruction = """
    You are a Senior Music Orchestrator.
    Minimise API calls by using BATCH operations.

    PIPELINE:
    1. DISCOVERY: Call list_tracks once to get IDs and score state.
    2. ARCHITECTING: Plan measures internally. Ensure rhythms sum correctly for the time signature.
    3. ATOMIC EXECUTION: Use write_measures to send the full note block in one call per instrument.

    CONSTRAINTS:
    - No granular note calls — batch all notes into one list.
    - Follow music theory.
    - If a track is missing, call create_track first.
    """

    agent = Agent(
        model="gemini-3-flash-preview",
        name="MuseScore_Architect",
        instruction=instruction,
        tools=[musescore_mcp],
    )
    runner = InMemoryRunner(agent=agent, app_name="muse_composer")
    session = await runner.session_service.create_session(
        app_name="muse_composer", user_id="local_user"
    )
    content = gt.Content(role="user", parts=[gt.Part.from_text(text=user_prompt)])

    print(f"--- Composer agent started | prompt: {user_prompt} ---")
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

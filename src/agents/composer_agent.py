import asyncio
import os
import sys

from dotenv import load_dotenv

# ADK Imports
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool import (
    McpToolset,
    StdioConnectionParams,
)
from google.genai import types
from mcp import StdioServerParameters


async def run_optimized_musescore_agent():
    # 1. Environment Setup
    load_dotenv()

    server_script = "mcp-musescore/server.py"
    if not os.path.exists(server_script):
        print(f"Error: {server_script} not found.")
        return

    # 2. Toolset Configuration
    musescore_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(command=sys.executable, args=[server_script]),
            timeout=30.0,
        )
    )

    # 3. Architect-Level Instructions
    # We move from "Protocol" to "Design Patterns" to reduce token bloat and errors.
    instruction = """
    You are a Senior Music Orchestrator. 
    Your goal is to minimize API calls by using BATCH operations.

    OPERATIONAL PIPELINE:
    1. DISCOVERY: Call 'list_tracks' once to get IDs and current score state. Identify Tracks.
    2. ARCHITECTING: Plan the 8 measures internally. Ensure rhythms sum correctly (e.g., 4/4 time).
    3. ATOMIC EXECUTION: Use 'write_measures' to send the entire block of notes in one call per instrument.
    
    CONSTRAINTS:
    - No granular note calls. If you must add 16 notes, send them as one list to the tool.
    - MUST follow music thoery
    - BE SIMPLISTIC
    - BUILD ON TOP of the current score
    - If a track is missing, call 'create_track' before writing.
    - Validate that your drum patterns align with the Moonlight Sonata triplets (12/8 or 4/4 triplets)
    - Execute via batch commands only."
    """

    agent = Agent(
        model="gemini-3-flash-preview",
        name="MuseScore_Architect",
        instruction=instruction,
        tools=[musescore_mcp],
    )

    # 4. Engine Initialization
    runner = InMemoryRunner(agent=agent, app_name="musescore_v2")

    try:
        session = await runner.session_service.create_session(
            app_name="musescore_v2", user_id="local_user"
        )

        user_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Write a random melody that makes sense"

        content = types.Content(
            role="user", parts=[types.Part.from_text(text=user_prompt)]
        )

        print(f"--- Orchestrator Session {session.id} Started ---")

        # 5. Execution Loop (Standard Generator)
        for event in runner.run(
            user_id="local_user", session_id=session.id, new_message=content
        ):
            if not event.content or not event.content.parts:
                continue

            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)

                if part.function_call:
                    # Visual feedback for the 'Batch' actions
                    print(f"\n[ORCHESTRATING: {part.function_call.name}]")

                if part.function_response:
                    print("[STATUS: Success]\n")

    except Exception as e:
        print(f"\n[RUNTIME ERROR]: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run_optimized_musescore_agent())

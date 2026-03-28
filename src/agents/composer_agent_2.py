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

    # Musescore Server (Runs in current environment)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    python_314 = (
        r"C:\Users\anton\code_and_projects\glitch\glitch\venv_314\Scripts\python.exe"
    )
    musescore_script = os.path.join(base_dir, "mcp-musescore", "server.py")
    if not os.path.exists(musescore_script):
        print(f"Error: {musescore_script} not found.")
        return

    # Audio Processor Server (Runs in Python 3.11 environment)
    python_311 = (
        r"C:\Users\anton\code_and_projects\glitch\glitch\venv_311\Scripts\python.exe"
    )
    audio_script = os.path.join(base_dir, "src", "audio", "audio_mcp_server.py")
    if not os.path.exists(audio_script):
        print(f"Error: {audio_script} not found.")
        return

    # 2. Toolset Configuration
    musescore_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=python_314, args=[musescore_script]
            ),
            timeout=300.0,
        )
    )

    audio_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=python_311, args=[audio_script]
            ),
            timeout=300.0,
        )
    )

    # 3. Architect-Level Instructions
    instruction = """
    You are a Senior Music Orchestrator and Transcription Expert. 
    Your goal is to process audio input into musical scores and minimize API calls by using BATCH operations.

    OPERATIONAL PIPELINE:
    1. TRANSCRIPTION: If the user provides an audio file, MUST use 'transcribe_crepe' to get the notes. This is the only allowed audio processing tool.
    2. DISCOVERY: Call 'list_tracks' once to get IDs and current score state. Identify Tracks.
    3. ARCHITECTING: Plan the measures internally based on the transcribed notes or user request. Ensure rhythms sum correctly (e.g., 4/4 time).
    4. ATOMIC EXECUTION: Use 'write_measures' to send the entire block of notes in one call per instrument.
    
    CONSTRAINTS:
    - No granular note calls. If you must add 16 notes, send them as one list to the tool.
    - MUST follow music theory.
    - If a track is missing, call 'create_track' before writing.
    - Validate that your drum patterns align with the triplets if specified.
    - Execute via batch commands only.
    """

    agent = Agent(
        model="gemini-3-flash-preview",
        name="MuseScore_Architect",
        instruction=instruction,
        tools=[musescore_mcp, audio_mcp],
    )

    # 4. Engine Initialization
    runner = InMemoryRunner(agent=agent, app_name="musescore_v2")

    try:
        session = await runner.session_service.create_session(
            app_name="musescore_v2", user_id="local_user"
        )

        user_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Listen to humming_demo.m4a and write it to the piano track."

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

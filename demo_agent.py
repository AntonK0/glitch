import asyncio
import json
import os
import re

from dotenv import load_dotenv

MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 30.0


def _parse_retry_delay(error: Exception) -> float:
    match = re.search(r"retry in (\d+(?:\.\d+)?)s", str(error))
    return float(match.group(1)) if match else DEFAULT_RETRY_DELAY


# ADK Imports
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool import (
    McpToolset,
    StdioConnectionParams,
)
import google.generativeai as genai
from google.genai import types
from mcp import StdioServerParameters

# ── Lyria config ──────────────────────────────────────────────────────────────
# Edit these to control what Lyria generates.
LYRIA_MOOD = "melancholic and nostalgic, like a distant memory"
LYRIA_STYLE = "solo piano, soft dynamics, gentle tempo"


LYRIA_MODEL = "lyria-3-clip-preview"
OUTPUT_FILE = "output_track.mp3"
# ─────────────────────────────────────────────────────────────────────────────


async def read_score_info() -> dict:
    """Use an ADK agent to gather track/tempo/time-signature info from MuseScore."""
    server_script = "mcp-musescore/server.py"
    if not os.path.exists(server_script):
        print(f"Error: {server_script} not found.")
        return {}

    musescore_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(command="python3", args=[server_script])
        )
    )

    instruction = """
    You are a score analyst. Your only job is to read the current MuseScore score and
    report every detail you find. Do the following in order:
    1. Call 'get_score_info' to get all instruments/tracks.
    2. Call 'go_to_beginning_of_score' to reset the cursor to the start.
    3. Walk through every element on every staff: repeatedly call 'get_cursor_info'
       to read the current element (recording staff index, measure number, pitch in MIDI,
       duration as numerator/denominator, and note vs rest), then call 'next_element'
       to advance. Stop when 'next_element' indicates the end of the score.
    4. Output a JSON array of all collected elements, then a plain-text summary of
       instrument names and what you observed.
    Do NOT add, delete, or modify any notes.
    """

    agent = Agent(
        model="gemini-3-flash-preview",
        name="ScoreReader",
        instruction=instruction,
        tools=[musescore_mcp],
    )

    runner = InMemoryRunner(agent=agent, app_name="score_reader")

    try:
        session = await runner.session_service.create_session(
            app_name="score_reader", user_id="local_user"
        )

        content = types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text="Scrape every note and beat from the score, then summarise it."
                )
            ],
        )

        print("--- Score Reader Started ---")
        summary_parts = []

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                for event in runner.run(
                    user_id="local_user", session_id=session.id, new_message=content
                ):
                    if not event.content or not event.content.parts:
                        continue
                    for part in event.content.parts:
                        if part.text:
                            print(part.text, end="", flush=True)
                            summary_parts.append(part.text)
                        if part.function_call:
                            print(f"\n[READING: {part.function_call.name}]")
                        if part.function_response:
                            print("[OK]\n")
                break  # success

            except Exception as e:
                err_str = str(e)
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                    delay = _parse_retry_delay(e)
                    if attempt < MAX_RETRIES:
                        print(
                            f"\n[RATE LIMITED] Retrying in {delay:.1f}s "
                            f"(attempt {attempt}/{MAX_RETRIES})..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        print(f"\n[RATE LIMITED] Max retries exhausted: {err_str}")
                else:
                    raise

        full_output = "".join(summary_parts).strip()

        # Extract JSON note array from agent output
        json_match = re.search(r"(\[[\s\S]*?\])", full_output)
        notes = json_match.group(1) if json_match else ""

        # Plain-text summary is everything after the JSON block
        summary = full_output[json_match.end():].strip() if json_match else full_output

        print(f"\n--- Score captured: {len(notes)} chars of notes, {len(summary)} chars of summary ---\n")
        return {"notes": notes, "summary": summary}

    except Exception as e:
        print(f"\n[SCORE READ ERROR]: {str(e)}")
        return {}


_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_DURATION_NAMES = {
    (4, 1): "whole", (2, 1): "double whole",
    (1, 1): "whole", (1, 2): "half", (1, 4): "quarter",
    (1, 8): "eighth", (1, 16): "sixteenth", (1, 32): "thirty-second",
    (3, 4): "dotted half", (3, 8): "dotted quarter", (3, 16): "dotted eighth",
}


def _midi_to_name(pitch: int) -> str:
    return f"{_NOTE_NAMES[pitch % 12]}{(pitch // 12) - 1}"


def _duration_to_name(num: int, den: int) -> str:
    return _DURATION_NAMES.get((num, den), f"{num}/{den}")


def _notes_json_to_description(notes_json: str) -> str:
    """Convert a JSON note array from the MCP into a human-readable sequence for Lyria."""
    try:
        elements = json.loads(notes_json)
    except (json.JSONDecodeError, TypeError):
        return notes_json  # fall back to raw if unparseable

    lines = []
    current_measure = None
    for el in elements:
        measure = el.get("measure", el.get("measure_number", "?"))
        staff = el.get("staff", el.get("staff_index", "?"))
        pitch = el.get("pitch")
        dur_num = el.get("duration", {}).get("numerator", 1) if isinstance(el.get("duration"), dict) else el.get("duration_numerator", 1)
        dur_den = el.get("duration", {}).get("denominator", 4) if isinstance(el.get("duration"), dict) else el.get("duration_denominator", 4)
        is_rest = el.get("is_rest", pitch is None or pitch == 0)

        if measure != current_measure:
            lines.append(f"\nMeasure {measure} (staff {staff}):")
            current_measure = measure

        dur_name = _duration_to_name(dur_num, dur_den)
        if is_rest:
            lines.append(f"  {dur_name} rest")
        else:
            lines.append(f"  {_midi_to_name(pitch)} {dur_name}")

    return "\n".join(lines)


async def generate_music_with_lyria(score_info: dict) -> None:
    """Generate a music track with Lyria and save it to OUTPUT_FILE."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set in environment / .env")
        return

    notes_json = score_info.get("notes", "")
    summary = score_info.get("summary", "")
    note_sequence = _notes_json_to_description(notes_json) if notes_json else "(no notes captured)"

    full_prompt = (
        f"You must play EXACTLY the following notes in EXACTLY this order with EXACTLY these durations. "
        f"Do not add, skip, reorder, or substitute any note. Do not improvise.\n\n"
        f"NOTE SEQUENCE:\n{note_sequence}\n\n"
        f"SCORE SUMMARY:\n{summary}\n\n"
        f"MOOD: {LYRIA_MOOD}\n"
        f"STYLE: {LYRIA_STYLE}\n\n"
        f"Render only the notes above — no introduction, no improvisation, no extra bars."
    )

    print(f"--- Lyria Prompt ---\n{full_prompt}\n--------------------")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(LYRIA_MODEL)

    print(f"Generating music with {LYRIA_MODEL}...")

    try:
        response = model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.7, "top_p": 0.95},
        )

        audio_parts = [
            p for c in response.candidates
            for p in c.content.parts
            if p.inline_data and p.inline_data.data
        ]
        if audio_parts:
            with open(OUTPUT_FILE, "wb") as f:
                for p in audio_parts:
                    f.write(p.inline_data.data)
            print(f"\n--- Audio saved to {OUTPUT_FILE} ---")
        else:
            print("No audio data returned.")

    except Exception as e:
        print(f"\n[LYRIA ERROR]: {str(e)}")


async def main():
    load_dotenv()

    # Step 1: Read the score
    score_info = await read_score_info()

    # Step 2: Generate music with Lyria
    await generate_music_with_lyria(score_info)


if __name__ == "__main__":
    asyncio.run(main())

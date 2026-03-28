import asyncio
import os
import sys
import wave

from dotenv import load_dotenv
from google import genai

# ADK Imports
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool import (
    McpToolset,
    StdioConnectionParams,
)
from google.genai import types
from mcp import StdioServerParameters


# Maps common key names to Lyria's Scale enum values
SCALE_MAP = {
    "C major":  "C_MAJOR_A_MINOR",  "A minor":  "C_MAJOR_A_MINOR",
    "Db major": "D_FLAT_MAJOR_B_FLAT_MINOR", "Bb minor": "D_FLAT_MAJOR_B_FLAT_MINOR",
    "D major":  "D_MAJOR_B_MINOR",  "B minor":  "D_MAJOR_B_MINOR",
    "Eb major": "E_FLAT_MAJOR_C_MINOR",      "C minor":  "E_FLAT_MAJOR_C_MINOR",
    "E major":  "E_MAJOR_D_FLAT_MINOR",      "Db minor": "E_MAJOR_D_FLAT_MINOR",
    "F major":  "F_MAJOR_D_MINOR",  "D minor":  "F_MAJOR_D_MINOR",
    "Gb major": "G_FLAT_MAJOR_E_FLAT_MINOR", "Eb minor": "G_FLAT_MAJOR_E_FLAT_MINOR",
    "G major":  "G_MAJOR_E_MINOR",  "E minor":  "G_MAJOR_E_MINOR",
    "Ab major": "A_FLAT_MAJOR_F_MINOR",      "F minor":  "A_FLAT_MAJOR_F_MINOR",
    "A major":  "A_MAJOR_G_FLAT_MINOR",      "Gb minor": "A_MAJOR_G_FLAT_MINOR",
    "Bb major": "B_FLAT_MAJOR_G_MINOR",      "G minor":  "B_FLAT_MAJOR_G_MINOR",
    "B major":  "B_MAJOR_A_FLAT_MINOR",      "Ab minor": "B_MAJOR_A_FLAT_MINOR",
}


async def generate_accompaniment(prompt: str, bpm: int, key: str, duration_seconds: float) -> str:
    """Generate a backing track with Lyria. Saves to accompaniment.wav.

    Args:
        prompt: Text description of the accompaniment style and mood.
        bpm: Tempo in beats per minute (60-200). Use the score's tempo exactly.
        key: Key of the piece e.g. 'C major', 'A minor', 'G major'. Used to lock Lyria's scale.
        duration_seconds: How long to generate in seconds. Calculate from the score:
            num_measures * beats_per_measure * 60 / bpm. Add 2 seconds of padding.
    """
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    client = genai.Client(
        api_key=api_key,
        http_options={"api_version": "v1alpha"},
    )
    audio_data = bytearray()

    # Clamp BPM to Lyria's supported range
    bpm = max(60, min(200, bpm))
    scale = SCALE_MAP.get(key, "C_MAJOR_A_MINOR")

    print(f'\n[LYRIA] prompt="{prompt}" bpm={bpm} scale={scale}\n')

    async with client.aio.live.music.connect(model="lyria-realtime-exp") as session:
        await session.set_music_generation_config(
            config=types.LiveMusicGenerationConfig(bpm=bpm, scale=scale)
        )
        await session.set_weighted_prompts(
            prompts=[types.WeightedPrompt(text=prompt, weight=1.0)]
        )
        await session.play()

        max_bytes = int(48000 * 2 * 2 * duration_seconds)
        async for message in session.receive():
            if message.server_content:
                for chunk in message.server_content.audio_chunks:
                    audio_data.extend(chunk.data)
            if len(audio_data) >= max_bytes:
                break

    output_path = "accompaniment.wav"
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(48000)
        wf.writeframes(bytes(audio_data))

    return f"Accompaniment saved to {output_path} (bpm={bpm}, scale={scale}, {len(audio_data) // 1000}KB)"


async def run_accompany_bot(user_prompt: str):
    load_dotenv()

    server_script = "mcp-musescore/server.py"
    if not os.path.exists(server_script):
        print(f"Error: {server_script} not found.")
        return

    musescore_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(command=sys.executable, args=[server_script]),
            timeout=30.0,
        )
    )

    instruction = f"""
    You are a music analyst and accompaniment generator.

    The user has requested: "{user_prompt}"

    STEPS — follow in order:

    1. Call get_score_info to see what instruments/staves exist.
    2. Call get_cursor_info to get the full score: all notes, pitches, durations, measures.
    3. Analyze the score:
       - Solo instrument: identify the primary melodic instrument (e.g. violin, flute, piano, cello, voice)
       - Key: most frequent pitch classes across all notes
       - Tempo BPM: look for Tempo/TempoText elements. If absent, infer from character
         (nursery rhyme ~100, ballad ~70, march ~120). Always an integer, never null.
       - Time signature: from beats per measure
       - Mood and energy: is it calm, bright, tense, sad, playful?
       - Rhythmic feel: steady, syncopated, waltz, triplet-based, etc.
       - Melody range: lowest to highest pitch

    4. Print the following:

    === SONG DETAILS ===
    Solo Instrument: <e.g. "violin">
    Key: <e.g. "C major">
    Time Signature: <e.g. 4/4>
    Tempo: <BPM integer>
    Melody Range: <lowest> to <highest note>
    Mood: <adjectives>
    Rhythmic Feel: <description>
    Existing Instruments: <list>

    === USER PROMPT ===
    <One sentence combining the song's mood/energy with the user's request: "{user_prompt}">

    === LYRIA ACCOMPANIMENT INSTRUCTIONS ===
    Lyria Prompt: "<You are writing an ACCOMPANIMENT, not background music or a standalone piece.
    The accompaniment must support and match the solo instrument identified above.
    Describe ONLY: accompaniment style suited to that instrument (e.g. piano left-hand arpeggios for violin,
    plucked strings for cello, soft pads for flute), mood, energy level, and 'no lead melody'.
    The result must sound like it is waiting for a soloist to play over it — not complete on its own.
    Do NOT mention chords or note names — Lyria ignores them.
    Example for violin: 'Flowing piano accompaniment with arpeggiated left hand, warm and expressive,
    romantic style, medium energy, no lead melody, supportive texture for solo violin.'>"
    Instruments to Include: <list — choose instruments that naturally accompany the solo instrument>
    Instruments to Avoid: <anything that doubles or competes with the solo melody>

    5. Call generate_accompaniment with:
       - prompt: the Lyria Prompt from step 4
       - bpm: integer BPM from step 3 (REQUIRED)
       - key: key string from step 3, e.g. "C major" (REQUIRED)
       - duration_seconds: find the last note in the score (highest offset + its duration),
         convert that total beat offset to seconds using (beat_offset * 60 / bpm), then add 2.
         Do NOT use num_measures * beats_per_measure — that overestimates if the score ends early.
    """

    agent = Agent(
        model="gemini-3-flash-preview",
        name="accompany_bot",
        instruction=instruction,
        tools=[musescore_mcp, generate_accompaniment],
    )

    runner = InMemoryRunner(agent=agent, app_name="accompany_bot")

    try:
        session = await runner.session_service.create_session(
            app_name="accompany_bot", user_id="local_user"
        )

        content = types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"Analyse the score and generate an accompaniment. User request: {user_prompt}"
                )
            ],
        )

        print("--- accompany_bot started ---\n")

        for event in runner.run(
            user_id="local_user", session_id=session.id, new_message=content
        ):
            if not event.content or not event.content.parts:
                continue

            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)

                if part.function_call:
                    if part.function_call.name == "generate_accompaniment":
                        print("\n[LYRIA CALL: generate_accompaniment]")
                    else:
                        print(f"\n[READING SCORE: {part.function_call.name}]")

                if part.function_response:
                    print("[DONE]\n")

    except Exception as e:
        print(f"\n[ERROR]: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python accompany_bot.py "<your prompt>"')
        print('Example: python accompany_bot.py "make it jazzy and upbeat"')
        sys.exit(1)

    user_prompt = sys.argv[1]
    asyncio.run(run_accompany_bot(user_prompt))

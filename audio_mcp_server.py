from mcp.server.fastmcp import FastMCP
import os
import sys

# Ensure current directory is in path so we can import our local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_parser import run_basic_pitch_transcription
from crepe_parser import run_crepe_transcription

mcp = FastMCP("AudioProcessor")

@mcp.tool()
def transcribe_basic_pitch(audio_path: str, onset_threshold: float = 0.6, frame_threshold: float = 0.4) -> str:
    """
    Transcribes audio (monophonic or polyphonic) to MIDI notes using Spotify's Basic Pitch.
    Returns a list of tuples: (start_time, end_time, midi_pitch).
    """
    if not os.path.exists(audio_path):
        return f"Error: File {audio_path} not found."
    
    try:
        notes = run_basic_pitch_transcription(
            audio_path, 
            onset_threshold=onset_threshold, 
            frame_threshold=frame_threshold
        )
        return str(notes)
    except Exception as e:
        return f"Error during Basic Pitch transcription: {str(e)}"

@mcp.tool()
def transcribe_crepe(audio_path: str, confidence_threshold: float = 0.8) -> str:
    """
    Transcribes monophonic audio (vocals, single instruments) to MIDI notes using CREPE.
    Best for high-precision pitch tracking.
    Returns a list of tuples: (start_time, end_time, midi_pitch).
    """
    if not os.path.exists(audio_path):
        return f"Error: File {audio_path} not found."
    
    try:
        notes = run_crepe_transcription(
            audio_path, 
            confidence_threshold=confidence_threshold
        )
        return str(notes)
    except Exception as e:
        return f"Error during CREPE transcription: {str(e)}"

if __name__ == "__main__":
    mcp.run()

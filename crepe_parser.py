import crepe
import librosa
import numpy as np
import os
import soundfile as sf
from notation_converter import convert_to_notation

def run_crepe_transcription(audio_path, confidence_threshold=0.8, min_note_duration=0.15):
    """
    Uses CREPE to track pitch and groups frames into note events.
    Best for MONOPHONIC audio (vocals, single instruments).
    
    Arguments:
    - confidence_threshold: 0.0 to 1.0. Higher = less noise/jitter (Default 0.8)
    - min_note_duration: Minimum seconds a note must last to be kept (Default 0.15s)
    """
    print(f"Analyzing {audio_path} with CREPE (Confidence: {confidence_threshold})...")
    
    # 1. Load audio (CREPE requires 16kHz)
    sr_target = 16000
    try:
        y, sr = librosa.load(audio_path, sr=sr_target)
    except Exception as e:
        # Fallback for m4a if system decoder fails
        print(f"Loading failed, trying fallback...")
        y, sr = librosa.load(audio_path, sr=sr_target, backend='audioread')
    
    # 2. Run CREPE
    # viterbi=True helps avoid octave jumps and makes tracking smoother
    time, frequency, confidence, activation = crepe.predict(y, sr, viterbi=True, step_size=10, verbose=False)
    
    # 3. Process the results into raw note segments
    raw_segments = []
    current_note = None
    start_time = None
    
    for i in range(len(time)):
        # Only process frames with high enough confidence
        if confidence[i] > confidence_threshold:
            midi_pitch = int(round(librosa.hz_to_midi(frequency[i])))
            
            if current_note is None:
                current_note = midi_pitch
                start_time = time[i]
            elif midi_pitch != current_note:
                # Note changed
                end_time = time[i]
                raw_segments.append((start_time, end_time, current_note))
                current_note = midi_pitch
                start_time = time[i]
        else:
            if current_note is not None:
                end_time = time[i]
                raw_segments.append((start_time, end_time, current_note))
                current_note = None
                start_time = None
                
    if current_note is not None:
        raw_segments.append((start_time, time[-1], current_note))
        
    # 4. Filter out jitter (extremely short notes)
    # We only keep notes that meet our duration threshold
    clean_notes = []
    for start, end, pitch in raw_segments:
        if (end - start) >= min_note_duration:
            clean_notes.append((start, end, pitch))
            
    return clean_notes

# --- Run the Parser ---
audio_path = "humming_demo.m4a"

try:
    # Using 0.80 for high precision
    notes = run_crepe_transcription(audio_path, confidence_threshold=0.8, min_note_duration=0.15)
    
    print("\n--- Parsed Notes (CREPE High-Confidence) ---", flush=True)
    if not notes:
        print("No notes found with current confidence threshold. Try lowering it if the audio is quiet.")
    
    for start, end, pitch in notes:
        duration = end - start
        note_name = librosa.midi_to_note(pitch).replace('♯', '#').replace('♭', 'b')
        print(f"Start: {start:05.2f}s | Note: {note_name:<3} | Duration: {duration:.2f}s", flush=True)

    # --- Convert to Notation ---
    print("\n" + "="*40)
    # Adjust BPM as needed for your humming speed
    musical_notes = convert_to_notation(notes, bpm=100)
    print("="*40)

except Exception as e:
    print(f"Error during CREPE transcription: {e}", flush=True)

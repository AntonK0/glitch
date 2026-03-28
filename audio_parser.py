from basic_pitch.inference import predict
import librosa
import numpy as np
import soundfile as sf
import os

def preprocess_audio(input_path, output_path):
    """
    Cleans audio by normalizing volume and applying a noise gate.
    """
    print(f"Pre-processing {input_path}...")
    
    # 1. Load the audio
    y, sr = librosa.load(input_path, sr=None)
    
    # 2. Normalize volume (sets peak to 1.0)
    y_norm = librosa.util.normalize(y)
    
    # 3. Save as a temporary wav file for the AI model
    sf.write(output_path, y_norm, sr)
    return output_path

# 1. Paths
audio_path = "humming_demo.m4a"
temp_wav_path = "processed_temp.wav"

# 2. Pre-process (Step 2 from suggestions)
# This converts compressed m4a to a clean wav for the AI
try:
    processed_path = preprocess_audio(audio_path, temp_wav_path)
except Exception as e:
    print(f"Warning: Pre-processing failed ({e}). Attempting direct analysis...")
    processed_path = audio_path

print(f"\nAnalyzing with Basic Pitch (Tuned Accuracy)...\n")

# 3. Run the AI model with Tuned Parameters (Step 1 from suggestions)
# onset_threshold: Higher (0.6) = more confident about note starts
# frame_threshold: Higher (0.4) = more confident about note sustain (prevents ghost notes)
# minimum_note_length: Filters out short accidental jitters (120ms)
model_output, midi_data, note_events = predict(
    processed_path,
    onset_threshold=0.6,
    frame_threshold=0.4,
    minimum_note_length=120
)

print("--- Parsed Notes & Rhythm ---")

# 4. Sort by start time and loop through the note events
# note_events is (start_time, end_time, pitch_midi, amplitude, pitch_bends)
sorted_notes = sorted(note_events, key=lambda x: x[0])

for note in sorted_notes:
    start_time = note[0]
    end_time = note[1]
    pitch_midi = note[2]
    duration = end_time - start_time
    readable_note = librosa.midi_to_note(pitch_midi)
    # Ensure standard text for Windows console (replaces sharp/flat symbols if they exist)
    clean_note = readable_note.replace('♯', '#').replace('♭', 'b')
    print(f"Start: {start_time:05.2f}s | Note: {clean_note:<3} | Duration: {duration:.2f}s")

# 5. Cleanup
if os.path.exists(temp_wav_path):
    os.remove(temp_wav_path)

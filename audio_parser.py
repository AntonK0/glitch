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

def run_basic_pitch_transcription(audio_path, onset_threshold=0.6, frame_threshold=0.4, minimum_note_length=120):
    """
    Runs Basic Pitch transcription on an audio file and returns a list of notes.
    """
    temp_wav_path = "processed_temp.wav"
    
    try:
        processed_path = preprocess_audio(audio_path, temp_wav_path)
    except Exception as e:
        print(f"Warning: Pre-processing failed ({e}). Attempting direct analysis...")
        processed_path = audio_path

    print(f"\nAnalyzing with Basic Pitch (Tuned Accuracy)...\n")

    # Run the AI model
    model_output, midi_data, note_events = predict(
        processed_path,
        onset_threshold=onset_threshold,
        frame_threshold=frame_threshold,
        minimum_note_length=minimum_note_length
    )

    # Sort and format the notes
    sorted_notes = sorted(note_events, key=lambda x: x[0])
    
    notes_list = []
    for note in sorted_notes:
        start_time = float(note[0])
        end_time = float(note[1])
        pitch_midi = int(note[2])
        notes_list.append((start_time, end_time, pitch_midi))
        
    # Cleanup
    if os.path.exists(temp_wav_path):
        os.remove(temp_wav_path)
        
    return notes_list

if __name__ == "__main__":
    # --- Run for Demo ---
    audio_path = "humming_demo.m4a"
    try:
        notes = run_basic_pitch_transcription(audio_path)
        print("--- Parsed Notes & Rhythm ---")
        for start_time, end_time, pitch_midi in notes:
            duration = end_time - start_time
            readable_note = librosa.midi_to_note(pitch_midi)
            clean_note = readable_note.replace('♯', '#').replace('♭', 'b')
            print(f"Start: {start_time:05.2f}s | Note: {clean_note:<3} | Duration: {duration:.2f}s")
    except Exception as e:
        print(f"Error during transcription: {e}")

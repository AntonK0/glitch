import librosa

def convert_to_notation(notes, bpm=120, resolution="16th"):
    """
    Converts raw time (seconds) to musical notation values through quantization.
    
    Arguments:
    - notes: List of (start_time, end_time, pitch_midi)
    - bpm: Beats per minute (Default 120)
    - resolution: The smallest note value to round to (Default "16th")
    """
    
    # 1. Calculate time durations for different note types
    quarter_note_dur = 60.0 / bpm
    
    # Grid definitions based on multiples of a 16th note
    if resolution == "16th":
        grid_unit = quarter_note_dur / 4
    elif resolution == "8th":
        grid_unit = quarter_note_dur / 2
    else:
        grid_unit = quarter_note_dur / 4 # Default to 16th
        
    # 2. Map of "units" to notation names
    # (units are multiples of the grid_unit)
    note_map = {
        16: "Whole",
        12: "Dotted Half",
        8:  "Half",
        6:  "Dotted Quarter",
        4:  "Quarter",
        3:  "Dotted Eighth",
        2:  "Eighth",
        1:  "16th"
    }
    
    print(f"--- Musical Notation (BPM: {bpm}, Grid: {resolution}) ---")
    
    quantized_output = []
    
    for start, end, pitch in notes:
        duration = end - start
        
        # 3. Quantize the duration
        # Divide by grid_unit and round to nearest whole unit
        units = max(1, round(duration / grid_unit))
        
        # Handle cases where duration might be longer than a whole note
        if units > 16:
            notation_name = "Whole+"
        else:
            # Find the closest match in our note_map
            closest_unit = min(note_map.keys(), key=lambda x: abs(x - units))
            notation_name = note_map[closest_unit]
            
        # 4. Quantize the start time (to find the beat position)
        beat_pos = (start / quarter_note_dur) + 1 # +1 to match 1-based measure counting
        measure = int((beat_pos - 1) // 4) + 1
        beat_in_measure = ((beat_pos - 1) % 4) + 1
        
        note_name = librosa.midi_to_note(pitch).replace('♯', '#').replace('♭', 'b')
        
        print(f"Meas {measure} | Beat {beat_in_measure:04.2f} | Note: {note_name:<3} | Value: {notation_name}")
        
        quantized_output.append({
            "measure": measure,
            "beat": beat_in_measure,
            "note": note_name,
            "value": notation_name,
            "units": units
        })
        
    return quantized_output

# --- Example Usage with Sample Data (from your humming demo) ---
if __name__ == "__main__":
    # Sample data: (start_time, end_time, pitch_midi)
    # These values match your last CREPE run for 'humming_demo.m4a'
    sample_notes = [
        (0.52, 0.71, 59), # B2
        (1.31, 1.49, 60), # C3
        (2.00, 2.33, 67), # G3
        (2.65, 2.92, 67), # G3
        (3.30, 3.59, 69), # A3
        (3.77, 4.07, 69), # A3
        (4.46, 4.97, 67)  # G3
    ]
    
    # Try with 100 BPM (typical for a nursery rhyme)
    convert_to_notation(sample_notes, bpm=100)

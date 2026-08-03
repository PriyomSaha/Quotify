"""
gender_tracker.py

Tracks character gender across reel generations to ensure fair rotation.
Uses a simple file-based counter to persist state between runs.
"""

import os
from pathlib import Path

TRACKER_FILE = Path.home() / ".cache" / "reel_gender_tracker.txt"

# Gender rotation sequence: M, F, N, M, F, N, M, F, N...
GENDER_SEQUENCE = ["male", "female", "none", "male", "female", "none"]


def _ensure_tracker_file():
    """Ensure tracker file and directory exist."""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not TRACKER_FILE.exists():
        TRACKER_FILE.write_text("0")


def get_next_gender():
    """
    Get the next gender in rotation sequence.
    Returns: "male", "female", or "none"
    """
    _ensure_tracker_file()
    
    # Read current index
    try:
        current_index = int(TRACKER_FILE.read_text().strip())
    except:
        current_index = 0
    
    # Get gender from sequence
    gender = GENDER_SEQUENCE[current_index % len(GENDER_SEQUENCE)]
    
    # Increment and save
    next_index = (current_index + 1) % len(GENDER_SEQUENCE)
    TRACKER_FILE.write_text(str(next_index))
    
    return gender


def get_gender_instruction(gender):
    """
    Convert gender code to detailed instruction for Gemini.
    """
    if gender == "male":
        return """
        CHARACTER GENDER: MALE (MANDATORY)
        
        Use a male character for this reel.
        - gender: "male"
        - age: Choose from: early 20s, late 20s, 30s, 40s, 50s, 60s, or 70s+
        - Vary the age - don't always use the same age group
        - Examples: young man, middle-aged man, elderly man, teenage boy
        - Clothing: casual, formal, traditional, or working clothes (context appropriate)
        - Keep consistent across all 6 scenes
        """
    
    elif gender == "female":
        return """
        CHARACTER GENDER: FEMALE (MANDATORY)
        
        Use a female character for this reel.
        - gender: "female"
        - age: Choose from: early 20s, late 20s, 30s, 40s, 50s, 60s, or 70s+
        - Vary the age - don't always use the same age group
        - Examples: young woman, middle-aged woman, elderly woman, teenage girl
        - Clothing: casual, formal, traditional, or working clothes (context appropriate)
        - Keep consistent across all 6 scenes
        """
    
    else:  # "none"
        return """
        CHARACTER: NO HUMAN CHARACTER (MANDATORY)
        
        Use abstract or nature-based visuals WITHOUT any human characters.
        - gender: "none"
        - age: "N/A"
        - hair: "N/A"
        - clothes: "N/A"
        
        Focus on environments, nature, objects, or abstract concepts:
        - Empty locations (bench, bridge, road, window)
        - Natural elements (ocean, sky, mountains, trees, rain, sunset)
        - Objects with meaning (cup of tea, old book, letter, photo frame)
        - Abstract concepts (light and shadow, time, seasons, silence)
        
        The visuals should evoke emotion through environment, not characters.
        """


def reset_tracker():
    """Reset the gender tracker (for testing)."""
    _ensure_tracker_file()
    TRACKER_FILE.write_text("0")


def get_current_stats():
    """Get current rotation position for debugging."""
    _ensure_tracker_file()
    try:
        index = int(TRACKER_FILE.read_text().strip())
        next_gender = GENDER_SEQUENCE[index % len(GENDER_SEQUENCE)]
        return {
            "index": index,
            "next_gender": next_gender,
            "sequence": GENDER_SEQUENCE
        }
    except:
        return {"index": 0, "next_gender": "male", "sequence": GENDER_SEQUENCE}


if __name__ == "__main__":
    # Test the rotation
    print("Gender Rotation Test:\n")
    
    for i in range(12):
        gender = get_next_gender()
        instruction = get_gender_instruction(gender)
        print(f"Generation {i+1}: {gender.upper()}")
        print(f"  Instruction: {instruction[:100]}...")
        print()
    
    # Reset for actual use
    reset_tracker()
    print("Tracker reset to start.")

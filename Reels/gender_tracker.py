"""
gender_tracker.py

Tracks reel visual modes across generations to keep image concepts diverse.
Uses random selection with equal male/female representation in the pool.
"""

import random
from pathlib import Path

TRACKER_FILE = Path.home() / ".cache" / "reel_visual_tracker.txt"

# Broader visual pool. Kept under the old module/function names for
# backwards compatibility with story_generation.py.
# Male and female appear once each so neither is favored.
VISUAL_SEQUENCE = [
    "nature",
    "female",
    "object",
    "rainy_city",
    "animal_life",
    "architecture",
    "abstract_emotion",
    "friends_or_couple",
    "nostalgic_room",
    "male",
    "nature",
    "object",
]

# Backwards-compatible alias used by older debug code.
GENDER_SEQUENCE = VISUAL_SEQUENCE


def _ensure_tracker_file():
    """Ensure tracker directory exists without forcing every fresh runner to index 0."""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_next_gender():
    """
    Pick a random visual mode.
    Returns modes such as: "nature", "female", "object", "rainy_city",
    "animal_life", "architecture", "abstract_emotion", "friends_or_couple",
    "nostalgic_room", or "male".
    """
    _ensure_tracker_file()

    visual_mode = random.choice(VISUAL_SEQUENCE)
    TRACKER_FILE.write_text(visual_mode)

    return visual_mode


def get_gender_instruction(gender):
    """
    Convert visual mode to detailed instruction for Gemini.
    """
    if gender == "male":
        return """
        VISUAL MODE: SINGLE MALE CHARACTER

        Use one male character only when the narration truly benefits from a person.
        - gender: "male"
        - age: vary naturally: early 20s, late 20s, 30s, 40s, 50s, 60s, or 70s+
        - clothes: simple, relatable, context-appropriate
        - keep him small-to-medium in frame, naturally inside the environment
        - avoid heroic poses, close-up portraits, selfies, and repeated sunset scenes
        - include varied locations like train platforms, rainy windows, fields, libraries, buses, rooftops, or quiet streets
        """

    if gender == "female":
        return """
        VISUAL MODE: SINGLE FEMALE CHARACTER

        Use one female character only when the narration truly benefits from a person.
        - gender: "female"
        - age: vary naturally: early 20s, late 20s, 30s, 40s, 50s, 60s, or 70s+
        - clothes: simple, relatable, context-appropriate
        - keep her small-to-medium in frame, naturally inside the environment
        - avoid glamour portraits, close-up faces, selfies, and repeated sunset scenes
        - include varied locations like rainy city streets, balconies with plants, cafes, libraries, buses, gardens, or rooftops
        """

    if gender == "friends_or_couple":
        return """
        VISUAL MODE: TWO PEOPLE / FRIENDS / COUPLE

        Use two ordinary people only if emotionally relevant.
        - gender: "mixed or unspecified"
        - age: choose realistic ages matching the narration
        - show natural distance/body language: walking, sitting, sharing tea, waiting at a station, or looking through a window
        - avoid over-romantic poses, wedding imagery, stereotypes, and close-up faces
        - keep the environment cinematic and emotionally important
        """

    if gender == "nature":
        return """
        VISUAL MODE: NATURE ONLY (MANDATORY)

        No human characters.
        - gender: "none"
        - age: "N/A"
        - hair: "N/A"
        - clothes: "N/A"
        - use natural elements as the main subject: forests, rivers, lakes, mountains, rain on leaves, clouds, moonlight, flowers, fields, ocean, snow, wind, morning mist
        - make every scene emotionally meaningful through weather, color, space, light, and movement
        - avoid using sunset in more than one scene
        """

    if gender == "object":
        return """
        VISUAL MODE: OBJECT STORY (MANDATORY)

        No human characters.
        - gender: "none"
        - age: "N/A"
        - hair: "N/A"
        - clothes: "N/A"
        - tell the emotion through objects: tea cup, diary, old letter, phone, umbrella, bicycle, photo frame, bus ticket, book, keys, shoes, lamp, empty chair
        - objects should sit in beautiful natural light or atmospheric interiors
        - avoid repeated cups-only scenes; vary the object each scene
        """

    if gender == "animal_life":
        return """
        VISUAL MODE: ANIMAL / NATURAL LIFE

        Prefer no human characters.
        - gender: "none"
        - age: "N/A"
        - hair: "N/A"
        - clothes: "N/A"
        - use gentle natural life: birds on wires, stray cat near a tea stall, dog sleeping near a shop, butterflies, fireflies, deer near trees, fish ripples, cows on a village road
        - keep it realistic, peaceful, and emotionally symbolic
        - no fantasy creatures, no aggressive animals
        """

    if gender == "architecture":
        return """
        VISUAL MODE: ARCHITECTURE / PLACE AS CHARACTER

        Usually no human characters; tiny distant people are allowed only for scale.
        - gender: "none"
        - age: "N/A"
        - hair: "N/A"
        - clothes: "N/A"
        - focus on quiet places: old train station, library corner, tea stall, balcony with plants, village street, cafe window, empty classroom, lighthouse, bridge, cabin
        - make the place feel lived-in, nostalgic, and aesthetic
        """

    if gender == "rainy_city":
        return """
        VISUAL MODE: RAINY CITY / MONSOON MOOD

        Human characters are optional and should be distant or subtle.
        - if no character: gender "none", age/hair/clothes "N/A"
        - focus on rain puddles, bus windows, wet streets, umbrellas, neon reflections, tea stalls, balconies, apartment windows
        - use monsoon atmosphere, soft reflections, and quiet loneliness
        - no crowded chaotic street scenes
        """

    if gender == "nostalgic_room":
        return """
        VISUAL MODE: NOSTALGIC ROOM / MEMORY INTERIOR

        Prefer no human characters.
        - gender: "none"
        - age: "N/A"
        - hair: "N/A"
        - clothes: "N/A"
        - focus on rooms and memory objects: old study desk, curtains, family photo frame, open notebook, warm lamp, empty bed, window light, plant shadows, childhood items
        - make the room feel quiet, personal, and emotionally warm
        """

    return """
        VISUAL MODE: ABSTRACT EMOTION / ENVIRONMENT ONLY

        No human characters.
        - gender: "none"
        - age: "N/A"
        - hair: "N/A"
        - clothes: "N/A"
        - express emotion through light, shadow, weather, empty spaces, seasons, doors, windows, roads, water, wind, and time
        - keep scenes concrete enough for illustration, not random symbols
        - avoid repeated sunset scenes
        """


def reset_tracker():
    """Clear the visual tracker debug file."""
    _ensure_tracker_file()
    TRACKER_FILE.write_text("")


def get_current_stats():
    """Get visual mode pool details for debugging."""
    _ensure_tracker_file()
    last_mode = TRACKER_FILE.read_text().strip() if TRACKER_FILE.exists() else ""
    return {
        "last_mode": last_mode or None,
        "next_gender": "random",
        "sequence": VISUAL_SEQUENCE,
        "male_count": VISUAL_SEQUENCE.count("male"),
        "female_count": VISUAL_SEQUENCE.count("female"),
    }


if __name__ == "__main__":
    # Test random visual mode selection
    print("Visual Mode Random Selection Test:\n")

    for i in range(12):
        gender = get_next_gender()
        instruction = get_gender_instruction(gender)
        print(f"Generation {i+1}: {gender.upper()}")
        print(f"  Instruction: {instruction[:100]}...")
        print()
    
    # Reset for actual use
    reset_tracker()
    print("Tracker reset to start.")

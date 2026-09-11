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
# Person-first pools; rainy_city appears once, never dominating.
VISUAL_SEQUENCE = [
    "landscape",
    "female",
    "bridge",
    "object",
    "male",
    "nature",
    "friends_or_couple",
    "architecture",
    "abstract_emotion",
    "nostalgic_room",
    "animal_life",
    "landscape",
    "bridge",
    "female",
]

# Backwards-compatible alias used by older debug code.
GENDER_SEQUENCE = VISUAL_SEQUENCE


def _ensure_tracker_file():
    """Ensure tracker directory exists without forcing every fresh runner to index 0."""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_next_gender(preferred_modes=None):
    """
    Pick a visual mode.

    - If preferred_modes is given (from the reel archetype), pick from that
      pool while avoiding the last used mode (no consecutive repeats).
    - Otherwise pick randomly from the broader VISUAL_SEQUENCE pool.
    Returns modes such as: "nature", "female", "object", "rainy_city",
    "animal_life", "architecture", "abstract_emotion", "friends_or_couple",
    "nostalgic_room", or "male".
    """
    _ensure_tracker_file()

    last_mode = TRACKER_FILE.read_text().strip() if TRACKER_FILE.exists() else ""

    pool = list(preferred_modes) if preferred_modes else list(VISUAL_SEQUENCE)

    # Avoid repeating the last mode back-to-back when the pool allows it.
    candidates = [mode for mode in pool if mode != last_mode]
    if not candidates:
        candidates = pool

    visual_mode = random.choice(candidates)
    TRACKER_FILE.write_text(visual_mode)

    return visual_mode


def get_gender_instruction(gender):
    """
    Convert visual mode to detailed instruction for Gemini.
    """
    if gender == "male":
        return """
        VISUAL MODE: ONE PERSON (male) DOING EVERYDAY TASKS

        A boy/man appears in MOST scenes doing simple honest tasks:
        - gender: "male"
        - age: vary naturally: early 20s, late 20s, 30s, 40s, 50s, 60s
        - task ideas (vary each scene): crossing a bridge, waiting at a bus
          stop, reading by a window, carrying groceries, talking on the phone,
          tying a shoelace, watering plants, walking a street at dusk, sitting
          on a bench, holding an umbrella, writing in a notebook
        - clothes: simple, relatable, context-appropriate
        - keep him small-to-medium in frame, naturally inside the environment
        - vary locations: bridge, train platform, fields, libraries, buses,
          rooftops, quiet streets, seaside, forest path
        - avoid heroic poses, close-up portraits, selfies, and repeated sunset scenes
        """

    if gender == "female":
        return """
        VISUAL MODE: ONE PERSON (female) DOING EVERYDAY TASKS

        A girl/woman appears in MOST scenes doing simple honest tasks:
        - gender: "female"
        - age: vary naturally: early 20s, late 20s, 30s, 40s, 50s, 60s
        - task ideas (vary each scene): crossing a bridge, watching rain from a
          bus window, reading by a window, tying her hair back, carrying a
          grocery bag, talking on the phone, watering plants, walking a street
          at dusk, sitting on a balcony, holding chai, writing in a notebook
        - clothes: simple, relatable, context-appropriate
        - keep her small-to-medium in frame, naturally inside the environment
        - vary locations: bridge, city street, balcony with plants, cafes,
          libraries, buses, gardens, rooftops, fields, seaside
        - avoid glamour portraits, close-up faces, selfies, and repeated sunset scenes
        """

    if gender == "friends_or_couple":
        return """
        VISUAL MODE: TWO PEOPLE / FRIENDS / COUPLE

        Two ordinary people doing an everyday thing together.
        - gender: "mixed or unspecified"
        - age: choose realistic ages matching the narration
        - show natural distance/body language: walking a bridge, sitting, sharing tea, waiting at a station, watching a window, walking a street at blue hour
        - keep the environment cinematic and emotionally important (river, city street, cafe, rooftop, field)
        - avoid over-romantic poses, wedding imagery, stereotypes, and close-up faces
        """

    if gender == "bridge":
        return """
        VISUAL MODE: ONE PERSON ON A BRIDGE

        A person (boy or girl) on or by a bridge in every key scene.
        - gender: plain "male" or "female"; vary across scenes naturally
        - show them crossing, standing, leaning on the railing, or stopping
          mid-way - usual everyday moments (looking at the water, a message on
          the phone, tying a shoelace, holding a cup, letting the wind hit)
        - bridges can be a footbridge over a river, a railway overpass, an old
          stone bridge in a village, a long highway bridge at blue hour
        - scenery (water, fields, city lights, mist, morning fog) is the
          beautiful background; the person's moment is the subject
        - avoid crowds; keep it calm, cinematic, and human
        """

    if gender == "landscape":
        return """
        VISUAL MODE: VAST LANDSCAPE WITH ONE SMALL PERSON

        Big nature with one small human in nearly every scene.
        - gender: plain "male" or "female"; vary naturally
        - the person is small-to-medium in the frame, doing an everyday thing:
          walking a mountain road, sitting on a field edge, cycling a village
          path, standing at a valley viewpoint, crossing a grassy plain, waiting
          at a railway crossing in open country
        - rotate scenery: misty mountains, endless rice fields, seaside cliffs,
          forest canopy, golden grassland, snow hills, lakeside, desert road at
          dawn - never the same landscape twice
        - let the scale of nature carry the emotion; the person gives it a soul
        - avoid sunset as the default; vary light: morning fog, high noon,
          blue hour, soft overcast, moonlight
        """

    if gender == "nature":
        return """
        VISUAL MODE: NATURE WITH ONE PERSON

        One ordinary person inside big nature in most scenes.
        - gender: plain "male" or "female"; vary naturally; age 20s-40s typical
        - the person is doing an everyday thing, not posing: walking a forest
          path, sitting by a river, resting under a tree, reading on a bench,
          cycling a village road, standing on a hillside
        - scenery (forests, rivers, lakes, mountains, clouds, moonlight,
          flowers, fields, ocean, snow, morning mist) is the beautiful setting
        - allow 1 of 6 scenes to be scenery-only for breathing room
        - avoid sunset in more than one scene; vary weather and light
        """

    if gender == "object":
        return """
        VISUAL MODE: OBJECT WITH ITS PERSON

        Every key object is shown being held or used by a person.
        - gender: plain "male" or "female"; vary naturally
        - one ordinary person interacts with the object: holding a steaming tea
          cup, writing in a diary, reading an old letter, holding a phone,
          gripping an umbrella, wheeling a bicycle, holding a photo frame,
          carrying a bus ticket, holding a book, turning keys
        - objects sit in beautiful natural light or atmospheric interiors
        - if a pure object-only scene fits (1 of 6 max), use it as a transition
        - avoid repeated cups-only scenes; vary the object and the task each scene
        """

    if gender == "animal_life":
        return """
        VISUAL MODE: ANIMALS WITH A PERSON NEARBY

        Gentle animal life with one ordinary person present in most scenes.
        - gender: plain "male" or "female" where a person appears (optional per scene)
        - the person shares the frame with gentle life: feeding birds on a
          wire, a stray cat near a tea stall the person sits at, a dog sleeping
          beside someone on a bench, butterflies near a walking path, cows on a
          village road the person walks past
        - keep it realistic, peaceful, warm, and emotionally symbolic
        - no fantasy creatures, no aggressive animals
        """

    if gender == "architecture":
        return """
        VISUAL MODE: PLACE WITH ONE PERSON FOR LIFE & SCALE

        A beautiful place with one ordinary person inside it.
        - gender: plain "male" or "female"; vary naturally
        - the person gives the place life: someone at a train station window,
          a person reading in a library corner, waiting at a tea stall, standing
          on a balcony with plants, walking a village street, at a cafe window,
          leaving an empty classroom, crossing a footbridge, at a lighthouse
        - focus on quiet places: old train station, library, tea stall, balcony,
          village street, cafe window, classroom, bridge, cabin
        - make the place feel lived-in, nostalgic, and aesthetic; the person
          small-to-medium in frame
        """

    if gender == "rainy_city":
        return """
        VISUAL MODE: RAINY CITY / MONSOON MOOD

        One ordinary person inside the rain (not scenery-only).
        - gender: plain "male" or "female"; vary naturally
        - the person does an everyday thing in the rain: holding an umbrella,
          watching from a bus window, crossing a wet street, waiting under a
          shop awning, pressing a phone to the ear under the metro shelter,
          stepping over puddles
        - focus on puddles, bus windows, wet streets, umbrellas, neon
          reflections, tea stalls, balconies, apartment windows
        - use monsoon atmosphere and soft reflections; keep the person's moment
          as the subject
        - no crowded chaotic street scenes
        """

    if gender == "nostalgic_room":
        return """
        VISUAL MODE: NOSTALGIC ROOM WITH ONE PERSON

        A room with one ordinary person living in it.
        - gender: plain "male" or "female"; vary naturally
        - show the person in honest quiet moments: writing at an old study desk,
          opening a window with the curtain moving, holding a family photo,
          reading an open notebook under a warm lamp, lying looking at the
          ceiling, making tea in a small kitchen, watering plant shadows
        - rooms and memory objects (desk, curtains, photo frame, notebook,
          lamp, empty bed, window light, plant shadows, childhood items) frame
          the person; the air must feel quiet, personal, warm
        """

    return """
        VISUAL MODE: ABSTRACT EMOTION WITH A PERSON

        One ordinary person carries the emotion in most scenes.
        - gender: plain "male" or "female"; vary naturally
        - express feeling through the person in light, shadow, weather, empty
          spaces, doors, windows, roads, water, and time: someone standing at a
          window, walking a road at dusk, sitting on a step, closing a door,
          staring at a ceiling, waiting at a crossing
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

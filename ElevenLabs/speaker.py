"""
speaker.py

Detects speaker gender and returns the best voice.
"""

from config import DEFAULT_FEMALE_VOICE, DEFAULT_MALE_VOICE

# ----------------------------------------------------
# Known Gender Words
# ----------------------------------------------------

FEMALE_WORDS = {
    "she",
    "her",
    "girl",
    "woman",
    "wife",
    "mother",
    "mom",
    "mum",
    "sister",
    "girlfriend",
    "daughter"
}

MALE_WORDS = {
    "he",
    "him",
    "boy",
    "man",
    "husband",
    "father",
    "dad",
    "brother",
    "boyfriend",
    "son"
}

# ----------------------------------------------------
# Common Female Names
# ----------------------------------------------------

FEMALE_NAMES = {
    "priya", "riya", "ria", "ananya", "kiara", "diya",
    "meera", "kavya", "pooja", "anjali", "tara", "zara",
    "emma", "ava", "mia", "luna", "ruby", "chloe",
    "bella", "sarah", "laura"
}

# ----------------------------------------------------
# Common Male Names
# ----------------------------------------------------

MALE_NAMES = {
    "arjun", "aarav", "kabir", "aditya", "kai",
    "liam", "noah", "oliver", "leo", "george",
    "charlie", "harry", "roger", "callum", "river"
}

# ----------------------------------------------------
# Unknown speaker memory
# ----------------------------------------------------

speaker_memory = {}
next_gender = "female"

# ----------------------------------------------------
# Detect Gender
# ----------------------------------------------------

def detect_gender(name: str) -> str:
    global next_gender

    key = name.strip().lower()

    if key in FEMALE_WORDS or key in FEMALE_NAMES:
        return "female"

    if key in MALE_WORDS or key in MALE_NAMES:
        return "male"

    if key in speaker_memory:
        return speaker_memory[key]

    gender = next_gender
    speaker_memory[key] = gender

    next_gender = "male" if next_gender == "female" else "female"

    return gender

# ----------------------------------------------------
# Voice Selection
# ----------------------------------------------------

def get_voice(name: str) -> str:

    gender = detect_gender(name)

    if gender == "female":
        return DEFAULT_FEMALE_VOICE

    return DEFAULT_MALE_VOICE

# ----------------------------------------------------
# Reset Memory
# ----------------------------------------------------

def reset_speakers():
    global next_gender

    speaker_memory.clear()
    next_gender = "female"
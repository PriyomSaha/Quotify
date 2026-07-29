"""
config.py
Configuration for Reel Generator
"""

import os
from pathlib import Path

# =====================================================
# PROJECT PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

TEMP_AUDIO_DIR = BASE_DIR / "temp_audio"
TEMP_FRAMES_DIR = BASE_DIR / "temp_frames"

TEMP_AUDIO_DIR.mkdir(exist_ok=True)
TEMP_FRAMES_DIR.mkdir(exist_ok=True)

# =====================================================
# ELEVENLABS
# =====================================================

# ELEVENLABS_API_KEY = os.getenv(
#     "ELEVENLABS_API_KEY",
#     "YOUR_ELEVENLABS_API_KEY"
# )

ELEVENLABS_API_KEY = "sk_3da8f78e2b57ddf466f154a07c329992feb1ae591aea99c8"

MODEL_ID = "eleven_multilingual_v2"

# =====================================================
# VOICES
# =====================================================

VOICES = {

    # Female
    "bella": {
        "id": "hpp4J3VqNfWAUOO0d1Us",
        "name": "Bella"
    },

    "sarah": {
        "id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Sarah"
    },

    "laura": {
        "id": "FGY2WhTYpPnrIDTdsKH5",
        "name": "Laura"
    },

    # Male
    "george": {
        "id": "JBFqnCBsd6RMkjVDRZzb",
        "name": "George"
    },

    "charlie": {
        "id": "IKne3meq5aSn9XLyUdCD",
        "name": "Charlie"
    },

    "roger": {
        "id": "CwhRBWXzGAHq8TQ4Fs17",
        "name": "Roger"
    },

    "callum": {
        "id": "N2lVS1w4EtoT3dr4eOWO",
        "name": "Callum"
    },

    "river": {
        "id": "SAz9YHcvj6GT2YYXdXww",
        "name": "River"
    },

    "harry": {
        "id": "SOYHLrjzK2X1ezoPC6cr",
        "name": "Harry"
    },

    "liam": {
        "id": "TX3LPaxmHKxFdv7VOQHJ",
        "name": "Liam"
    }

}

# =====================================================
# DEFAULT VOICES
# =====================================================

DEFAULT_FEMALE_VOICE = VOICES["bella"]["id"]
DEFAULT_MALE_VOICE = VOICES["george"]["id"]

# =====================================================
# OUTPUT FILES
# =====================================================

VOICEOVER_FILE = BASE_DIR / "voiceover.mp3"
OUTPUT_VIDEO = BASE_DIR / "reel.mp4"

# =====================================================
# VIDEO
# =====================================================

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# =====================================================
# AUDIO
# =====================================================

SILENCE_BETWEEN_MESSAGES_MS = 250
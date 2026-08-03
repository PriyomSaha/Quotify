"""
config.py

Central configuration for the Reel Generator.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ----------------------------
# Gemini
# ----------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-3.6-flash"

# ----------------------------
# Hugging Face
# ----------------------------

HF_TOKEN = os.getenv("HF_TOKEN")
HF_TOKEN_2 = os.getenv("HF_TOKEN2")  # Optional backup token
# HF_TOKEN_3 = os.getenv("HF_TOKEN_3")  # Optional backup token

HF_MODEL = "black-forest-labs/FLUX.1-schnell"

HF_PROVIDER = "fal-ai"

# ----------------------------
# Cloudflare (Fallback)
# ----------------------------

# CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID_1")
# CF_TOKEN = os.getenv("CF_TOKEN_1")

# CF_ACCOUNT_ID_2 = os.getenv("CF_ACCOUNT_ID_2")
# CF_TOKEN_2 = os.getenv("CF_TOKEN_2")

# CF_ACCOUNT_ID_3 = os.getenv("CF_ACCOUNT_ID_3")
# CF_TOKEN_3 = os.getenv("CF_TOKEN_3")

# CF_ACCOUNT_ID_4 = os.getenv("CF_ACCOUNT_ID_4")
# CF_TOKEN_4 = os.getenv("CF_TOKEN_4")

# CF_ACCOUNT_ID_5 = os.getenv("CF_ACCOUNT_ID_5")
# CF_TOKEN_5 = os.getenv("CF_TOKEN_5")

# CF_ACCOUNT_ID_6 = os.getenv("CF_ACCOUNT_ID_6")
# CF_TOKEN_6 = os.getenv("CF_TOKEN_6")

# CF_MODEL = "@cf/black-forest-labs/flux-1-schnell"

# ----------------------------
# ElevenLabs
# ----------------------------

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

ELEVEN_MODEL = "eleven_multilingual_v2"

VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

# ----------------------------
# Video
# ----------------------------

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
IMAGE_ZOOM = 1.08
IMAGE_FADE = 0.4
BITRATE = "8000k"
FILM_GRAIN_INTENSITY = 18
DARK_OVERLAY_OPACITY = 45
ZOOM_DIRECTION = "in"

# ----------------------------
# Music
# ----------------------------

BACKGROUND_MUSIC = BASE_DIR / "inputs" / "background.mp3"  # Check inputs folder first

MUSIC_VOLUME = 0.15

# ----------------------------
# Subtitle
# ----------------------------

FONT = str((BASE_DIR.parent / "Fonts" / "Montserrat" / "static" / "Montserrat-Light.ttf"))
FONT_SIZE = 64

FONT_COLOR = "white"

STROKE_COLOR = "black"

STROKE_WIDTH = 3

BOTTOM_MARGIN = 450  # Increased - text positioned higher from bottom

# ----------------------------
# LOGO
# ----------------------------
LOGO_TEXT = "FB : Aesthetic Vibes \nIG: @aesthetic_o_vibes"
LOGO_FONT = str((BASE_DIR.parent / "Fonts" / "Kaushan_Script" / "KaushanScript-Regular.ttf"))
LOGO_FONT_SIZE = 45
LOGO_FONT_COLOR = (255, 32, 117)  # #FF2075 - bright pink

# ----------------------------
# Generation
# ----------------------------

SCENE_COUNT = 6

MIN_WORDS = 80

MAX_WORDS = 120

# ----------------------------
# Retry
# ----------------------------

MAX_RETRIES = 3

RETRY_DELAY = 5

REQUEST_TIMEOUT = 120
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

# Check if running on Render (low-resource environment)
IS_RENDER = os.getenv("RENDER") is not None

if IS_RENDER:
    # Ultra-optimized settings for Render's 512MB RAM limit
    # Maintaining 9:16 aspect ratio for Instagram Reels
    VIDEO_WIDTH = 540  # Much lower resolution to fit in 512MB RAM
    VIDEO_HEIGHT = 960  # 540x960 maintains 9:16 ratio
    FPS = 20  # Lower FPS for memory efficiency
    BITRATE = "2000k"  # Lower bitrate
    FILM_GRAIN_INTENSITY = 0  # Disable grain (memory intensive)
    IMAGE_ZOOM = 1.0  # Disable Ken Burns zoom (CPU/memory intensive)
    # Scale font size proportionally (540/1080 = 0.5x scale)
    FONT_SIZE = 32  # Half of 64 for half resolution
    LOGO_FONT_SIZE = 22  # Half of 45
    BOTTOM_MARGIN = 110  # Watermark gap from bottom (shifted down a few cm)
    TOP_MARGIN = VIDEO_HEIGHT // 2 + FONT_SIZE - 50  # Subtitles ~1 line below the middle
else:
    # High quality settings for local/powerful servers
    # Perfect 9:16 ratio for Instagram Reels
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920  # 1080x1920 is 9:16
    FPS = 30
    BITRATE = "8000k"
    FILM_GRAIN_INTENSITY = 18
    IMAGE_ZOOM = 1.08
    FONT_SIZE = 64
    LOGO_FONT_SIZE = 45
    BOTTOM_MARGIN = 220  # Watermark gap from bottom (shifted down a few cm)
    TOP_MARGIN = VIDEO_HEIGHT // 2 + FONT_SIZE - 50  # Subtitles ~1 line below the middle

IMAGE_FADE = 0.4
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

# FONT = str((BASE_DIR.parent / "Fonts" / "Montserrat" / "static" / "Montserrat-Light.ttf"))
FONT = str((BASE_DIR.parent / "Fonts" / "Caveat" / "static" / "Caveat-Regular.ttf"))
# FONT_SIZE is set above based on IS_RENDER (32 for low-res, 64 for high-res)

FONT_COLOR = "white"

STROKE_COLOR = "black"

STROKE_WIDTH = 3

# BOTTOM_MARGIN is set above based on IS_RENDER (shifts watermark down from the bottom edge)
# TOP_MARGIN places subtitles ~1 line below the video midpoint

# ----------------------------
# LOGO
# ----------------------------
LOGO_TEXT = "FB : Aesthetic Vibes \nIG: @aesthetic_o_vibes"
LOGO_FONT = str((BASE_DIR.parent / "Fonts" / "Kaushan_Script" / "KaushanScript-Regular.ttf"))
# LOGO_FONT_SIZE is set above based on IS_RENDER (22 for low-res, 45 for high-res)
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

# ----------------------------
# Upload to Social Media
# ----------------------------

# Control whether to upload reels to Facebook and Instagram after generation
# Set to "true" or "false" in .env file
# Default: true (upload enabled)
AUTO_UPLOAD_REELS = os.getenv("AUTO_UPLOAD_REELS", "true").lower() == "true"
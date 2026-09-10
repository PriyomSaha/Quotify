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

# ----------------------------
# Gemini
# ----------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-3.6-flash"

# ----------------------------
# Video
# ----------------------------

# Perfect 9:16 ratio for Instagram Reels
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # 1080x1920 is 9:16
FPS = 30
BITRATE = "8000k"
FILM_GRAIN_INTENSITY = 18
FONT_SIZE = 70
LOGO_FONT_SIZE = 18
BOTTOM_MARGIN = 60  # Watermark gap from bottom (shifted down a few cm)
TOP_MARGIN = VIDEO_HEIGHT // 2 + FONT_SIZE - 500  # Subtitles ~1 line below the middle

DARK_OVERLAY_OPACITY = 0.20

# ----------------------------
# Cinematic Effects (tweakable)
# ----------------------------

# Ken Burns zoom range (1.0 = no zoom)
ZOOM_MIN = 1.00
ZOOM_MAX = 1.08

# Film grain added to every frame
FILM_GRAIN_AMOUNT = 20

# Crossfade duration in seconds between scene images
CROSSFADE_DURATION = 0.5

# End card (profile) duration in seconds after narration finishes
END_CARD_DURATION = 3.0

# Subtitle readability / timing
SUBTITLE_MIN_DURATION = 1.5   # Minimum seconds a subtitle stays visible
SUBTITLE_HOLD_TIME = 0.8       # Extra seconds kept on screen after speech ends
SUBTITLE_FADE = 0.2            # Subtitle fade in/out duration (seconds)
SUBTITLE_MAX_WIDTH_OFFSET = 120  # Pixels subtracted from video width (text area)
SUBTITLE_PADDING = 30          # Padding around subtitle text
SUBTITLE_LINE_SPACING = 12     # Vertical gap between subtitle lines

# End card colors/layout
END_CARD_BG_COLOR = (20, 20, 30)  # Dark blue-grey
PROFILE_PIC_SIZE = 400            # End card profile image size (px)
PROFILE_FADE_IN = 0.3             # Profile photo fade-in duration (seconds)

# Watermark (logo) appearance
WATERMARK_IMG_HEIGHT = 300        # Watermark strip height (px)
WATERMARK_OPACITY = 0.50          # Watermark opacity (0.0 - 1.0)
WATERMARK_GLOW_ALPHA = 200        # Glow layer alpha (0 - 255)
WATERMARK_TEXT_ALPHA = 230        # Main text alpha (0 - 255)
WATERMARK_GLOW_BLUR_RADIUS = 10   # Glow blur radius (px)

# ----------------------------
# Music
# ----------------------------

BACKGROUND_MUSIC = BASE_DIR / "inputs" / "background.mp3"  # Check inputs folder first

MUSIC_VOLUME = 0.15

# ----------------------------
# Subtitle
# ----------------------------

FONT = str((BASE_DIR.parent / "Fonts" / "Caveat" / "static" / "Caveat-Regular.ttf"))

FONT_COLOR = "white"

STROKE_COLOR = "black"

STROKE_WIDTH = 3

# ----------------------------
# LOGO
# ----------------------------
LOGO_TEXT = "FB : Aesthetic Vibes \nIG: @aesthetic_o_vibes"
LOGO_FONT = str((BASE_DIR.parent / "Fonts" / "Kaushan_Script" / "KaushanScript-Regular.ttf"))
LOGO_FONT_COLOR = (255, 32, 117)  # #FF2075 - bright pink

# ----------------------------
# Upload to Social Media
# ----------------------------

# Control whether to upload reels to Facebook and Instagram after generation
# Set to "true" or "false" in .env file
# Default: true (upload enabled)
AUTO_UPLOAD_REELS = os.getenv("AUTO_UPLOAD_REELS", "true").lower() == "true"
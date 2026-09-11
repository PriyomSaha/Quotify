from typing import Optional

import asyncio
from datetime import datetime
import json
from pathlib import Path
import re
import edge_tts

# Assuming these exist in your project structure
from .config import OUTPUT_DIR
from .image_generation import generate_images_for_reel
from .story_generation import generate_story
from .video_generation import create_reel

# VOICE CONFIGURATION: Microsoft Edge-TTS
# 'en-US-GuyNeural' - Natural, mature male voice
# Perfect for wisdom, life advice, and philosophical content
# EDGE_VOICE = "en-US-GuyNeural"
# FIXED_VOICE_NAME = "Guy (Mature, Natural)"

# # Voice modulation for slower, deeper delivery
# VOICE_RATE = "-10%"  # Slower for thoughtful delivery
# VOICE_PITCH = "-3Hz"  # Slightly lower for depth

# EDGE_VOICE = "en-US-BrianNeural"
# FIXED_VOICE_NAME = "Brian"
# VOICE_RATE = "-13%"
# VOICE_PITCH = "-3Hz"
# VOLUME = "+10%"

# EDGE_VOICE = "en-US-AndrewNeural"
# FIXED_VOICE_NAME = "AndrewNeural"
# VOICE_RATE = "-18%"
# VOICE_PITCH = "-2Hz"
# VOLUME = "+10%"

# ============================================================================
# VOICE PROFILES - rotate by reel archetype so the voice never goes stale
# ============================================================================
# Keyed by the "voice" value the PromptSelector archetypes emit:
#   calm_male     - default brand voice (the original Ryan)
#   deep_male     - deeper, older stories / real talk
#   warm_female   - hope, letters, quiet joy
#   soft_female   - Indian-accented warmth, desi slice-of-life
VOICE_PROFILES = {
    "calm_male": {
        "name": "Ryan (en-GB calm)",
        "voice": "en-GB-RyanNeural",
        "rate": "-15%",
        "pitch": "-5Hz",
        "volume": "+10%",
    },
    "deep_male": {
        "name": "Guy (en-US deep)",
        "voice": "en-US-GuyNeural",
        "rate": "-12%",
        "pitch": "-4Hz",
        "volume": "+10%",
    },
    "warm_female": {
        "name": "Sonia (en-GB warm)",
        "voice": "en-GB-SoniaNeural",
        "rate": "-10%",
        "pitch": "+0Hz",
        "volume": "+10%",
    },
    "soft_female": {
        "name": "Neerja (en-IN warm)",
        "voice": "en-IN-NeerjaNeural",
        "rate": "-12%",
        "pitch": "+0Hz",
        "volume": "+10%",
    },
}

DEFAULT_VOICE_KEY = "calm_male"

def get_voice_profile(voice_key: Optional[str] = None) -> dict:
    """Return the voice profile for an archetype, falling back to the default."""
    if voice_key and voice_key in VOICE_PROFILES:
        return VOICE_PROFILES[voice_key]
    return VOICE_PROFILES[DEFAULT_VOICE_KEY]


# Backwards-compatible aliases (the original default voice):
FIXED_VOICE_NAME = VOICE_PROFILES[DEFAULT_VOICE_KEY]["name"]
EDGE_VOICE = VOICE_PROFILES[DEFAULT_VOICE_KEY]["voice"]
VOICE_RATE = VOICE_PROFILES[DEFAULT_VOICE_KEY]["rate"]
VOICE_PITCH = VOICE_PROFILES[DEFAULT_VOICE_KEY]["pitch"]
VOLUME = VOICE_PROFILES[DEFAULT_VOICE_KEY]["volume"]

# FIXED_VOICE_NAME = "ChristopherNeural"
# EDGE_VOICE = "en-US-ChristopherNeural"
# VOICE_RATE = "-12%"
# VOICE_PITCH = "-0Hz"
# VOLUME = "+10%"

def clean_and_slow_text(text: str) -> str:
    """
    Cleans up whitespace and optimizes text structure for natural narrative pacing.
    """
    if not text:
        return ""
    # Standardize spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def generate_voice_edge(text: str, output_file: str, voice_profile: dict):
    """Asynchronous runner to communicate with the free Edge-TTS servers."""
    paced_text = clean_and_slow_text(text)
    communicate = edge_tts.Communicate(
        text=paced_text,
        voice=voice_profile["voice"],
        rate=voice_profile["rate"],
        pitch=voice_profile["pitch"],
        volume=voice_profile["volume"]
    )
    await communicate.save(output_file)

def generate_voice(text: str, output_file="output.mp3", voice: Optional[str] = None):
    """
    Synchronous wrapper matching your pipeline layout exactly.
    Safe for low-spec cloud deployments like Render & GitHub Actions.

    Args:
        voice: optional archetype voice key ("deep_male", "warm_female", ...).
              None = the classic Ryan calm default.
    """
    profile = get_voice_profile(voice)
    try:
        asyncio.run(generate_voice_edge(text, output_file, profile))
        print("=" * 50)
        print("Voice Generated Successfully (Edge-TTS Cloud)")
        print("=" * 50)
        print(f"Voice profile : {profile['name']}")
        print(f"Voice key     : {voice or DEFAULT_VOICE_KEY}")
        print(f"Saved To      : {output_file}\n")
        return output_file
    except Exception as e:
        raise RuntimeError(f"Cloud Voice Generation Failed: {str(e)}")

# ==========================================================
# MAIN EXECUTION PIPELINE
# ==========================================================
if __name__ == "__main__":
    timestamp = "20260802_135618"
    OUTPUT_DIR = Path("output")
    story_file = Path(f"/Users/priyom_saha/Documents/QuotesGenerator/Reels/output/{timestamp}/story.json")
    audio_path = Path(f"/Users/priyom_saha/Documents/QuotesGenerator/Reels/output/{timestamp}/voiceover_{EDGE_VOICE}.mp3")

    print("📖 Loading existing story...\n")
    with open(story_file, "r", encoding="utf-8") as f:
        story = json.load(f)

    print("🎤 Testing Voice...\n")
    generate_voice(
        text=story["narration"],
        output_file=str(audio_path)
    )

    print("\n✅ Voice Generated")
    print(f"📄 Story : {story_file}")
    print(f"🎤 Audio : {audio_path}")

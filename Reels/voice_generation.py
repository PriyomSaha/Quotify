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
# VOICE CONFIGURATION - Microsoft Edge-TTS (single fixed voice)
# ============================================================================
# 'en-GB-RyanNeural' - Natural, calm British male voice
FIXED_VOICE_NAME = "RyanNeural"
EDGE_VOICE = "en-GB-RyanNeural"
VOICE_RATE = "-15%"   # Slower for thoughtful delivery
VOICE_PITCH = "-5Hz"  # Slightly lower for depth
VOLUME = "+10%"

# Kept for backwards compatibility with callers that pass an archetype
# voice key (e.g. story.get("voice")). IGNORED - only Ryan is used.
def get_voice_profile(voice_key: Optional[str] = None) -> dict:
    """Return the single fixed Ryan voice profile (archetype keys are ignored)."""
    return {
        "name": FIXED_VOICE_NAME,
        "voice": EDGE_VOICE,
        "rate": VOICE_RATE,
        "pitch": VOICE_PITCH,
        "volume": VOLUME,
    }

DEFAULT_VOICE_KEY = "calm_male"

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

    Always uses the single fixed Ryan voice. The ``voice`` argument is
    accepted for signature compatibility and IGNORED.

    Args:
        voice: ignored (kept so existing callers don't break).
    """
    profile = get_voice_profile()
    try:
        asyncio.run(generate_voice_edge(text, output_file, profile))
        print("=" * 50)
        print("Voice Generated Successfully (Edge-TTS Cloud)")
        print("=" * 50)
        print(f"Voice profile : {profile['name']}")
        print(f"Voice         : {profile['voice']}")
        print(f"Saved To      : {output_file}\n")
        return output_file
    except Exception as e:
        raise RuntimeError(f"Cloud Voice Generation Failed: {str(e)}")

# ==========================================================
# MAIN EXECUTION PIPELINE
# ==========================================================
if __name__ == "__main__":
    timestamp = "20260911_134942"
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

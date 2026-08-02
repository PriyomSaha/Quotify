import asyncio
from datetime import datetime
import json
from pathlib import Path
import re
import edge_tts

# Assuming these exist in your project structure
from config import OUTPUT_DIR
from image_generation import generate_images_for_reel
from story_generation import generate_story
from video_generation import create_reel

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

FIXED_VOICE_NAME = "RyanNeural"
EDGE_VOICE = "en-GB-RyanNeural"
VOICE_RATE = "-15%"
VOICE_PITCH = "-5Hz"
VOLUME = "+10%"

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

async def generate_voice_edge(text: str, output_file: str):
    """
    Asynchronous runner to communicate with the free Edge-TTS servers.
    """
    paced_text = clean_and_slow_text(text)
    
    communicate = edge_tts.Communicate(
        text=paced_text, 
        voice=EDGE_VOICE, 
        rate=VOICE_RATE, 
        pitch=VOICE_PITCH,
        volume=VOLUME
    )
    await communicate.save(output_file)

def generate_voice(text: str, output_file="output.mp3"):
    """
    Synchronous wrapper matching your pipeline layout exactly.
    Safe for low-spec cloud deployments like Render & GitHub Actions.
    """
    try:
        asyncio.run(generate_voice_edge(text, output_file))
        
        print("=" * 50)
        print("Voice Generated Successfully (Edge-TTS Cloud)")
        print("=" * 50)
        print(f"Voice Locked : {FIXED_VOICE_NAME}")
        print(f"Saved To     : {output_file}\n")
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

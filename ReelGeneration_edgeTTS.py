"""
ReelGeneration.py - Create Instagram Reels from chat conversations
Uses Edge TTS for natural Indian English voices
"""

import asyncio
import edge_tts
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

# Voice mapping based on names
FEMALE_NAMES = {
    'Priya', 'Ananya', 'Saanvi', 'Aadhya', 'Diya', 'Kiara', 'Navya', 'Riya', 'Avni', 'Myra',
    'Ria', 'Tithi', 'Piya', 'Sanjana', 'Meera', 'Kavya', 'Divya', 'Nithya', 'Srishti', 'Anjali',
    'Pooja', 'Zara', 'Tara', 'Mila', 'Sienna', 'Elara', 'Mia', 'Nora', 'Chloe', 'Zoe', 'Ava',
    'Emma', 'Isla', 'Luna', 'Ivy', 'Aria', 'Lyra', 'Willow', 'Ruby', 'Eliza', 'Stella', 'Aurora',
    'Hana', 'Yuki', 'Mei', 'Kira', 'Nova', 'Sage', 'Riley', 'Eden', 'Skylar', 'Dakota', 'Jules',
    'Reese', 'Avery', 'Morgan', 'Parker', 'Rowan', 'Ember', 'Taylor', 'Casey', 'Cameron', 'Kendall',
    'Peyton', 'Stevie', 'Charlie', 'Frankie', 'Blair', 'Hayden', 'Emerson', 'Astra', 'Indie', 'Hazel'
}

MALE_NAMES = {
    'Arjun', 'Aarav', 'Vihaan', 'Reyansh', 'Vivaan', 'Ishaan', 'Atharv', 'Aditya', 'Kabir', 'Advait',
    'Ayan', 'Aryan', 'Anik', 'Rudra', 'Karthik', 'Pranav', 'Surya', 'Bibek', 'Aayush', 'Sandesh',
    'Kai', 'River', 'Phoenix', 'Blake', 'Quinn', 'Jax', 'Finn', 'Leo', 'Theo', 'Liam', 'Ethan',
    'Noah', 'Oliver', 'Orion', 'Atlas', 'Jasper', 'Felix', 'Oscar', 'Milo', 'Asher', 'Hugo', 'Silas',
    'Akira', 'Haru', 'Min', 'Ren', 'Sam', 'Jordan', 'Drew'
}

# Indian English voices (natural sounding)
VOICE_FEMALE = "en-IN-NeerjaNeural"  # Warm, emotional female
VOICE_MALE = "en-IN-PrabhatNeural"    # Deep, confident male


def get_voice_for_name(name):
    """Determine voice based on name"""
    if name in FEMALE_NAMES:
        return VOICE_FEMALE
    elif name in MALE_NAMES:
        return VOICE_MALE
    else:
        # Default to female for gender-neutral names
        return VOICE_FEMALE


def generate_voiceover_sync(conversation_lines, output_file="voiceover.mp3"):
    """
    Generate voiceover for conversation - synchronous wrapper
    
    conversation_lines: [(name, text), (name, text), ...]
    """
    
    async def _generate():
        # Build simple text with natural pauses
        text_parts = []
        
        for name, text in conversation_lines:
            # Add the dialogue text
            text_parts.append(text)
        
        # Combine with pauses (periods add natural pauses)
        full_text = ". ".join(text_parts)
        
        # Use Indian English female voice (natural sounding)
        communicate = edge_tts.Communicate(
            full_text,
            VOICE_FEMALE,
            rate="+0%",  # Normal speed
            pitch="+0Hz"  # Normal pitch
        )
        await communicate.save(output_file)
    
    # Run async function synchronously
    asyncio.run(_generate())
    
    print(f"✅ Voiceover generated: {output_file}")
    return output_file


def create_chat_bubble_frame(name, text, is_sender=True, width=1080, height=1920):
    """
    Create a single chat bubble frame
    
    is_sender: True = right side (pink), False = left side (gray)
    """
    
    # Create dark background
    img = Image.new('RGB', (width, height), color=(20, 20, 25))
    draw = ImageDraw.Draw(img)
    
    # Load font
    try:
        BASE_DIR = Path(__file__).resolve().parent
        FONT_PATH = BASE_DIR / "Montserrat" / "static" / "Montserrat-Light.ttf"
        font_name = ImageFont.truetype(str(FONT_PATH), 32)
        font_text = ImageFont.truetype(str(FONT_PATH), 48)
    except:
        font_name = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    # Chat bubble settings
    bubble_width = 800
    padding = 40
    margin = 60
    
    # Wrap text
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_text = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), test_text, font=font_text)
        if bbox[2] - bbox[0] > bubble_width - padding * 2:
            current_line.pop()
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Calculate bubble height
    line_height = 60
    bubble_height = padding * 2 + len(lines) * line_height + 50
    
    # Position bubble
    if is_sender:
        # Right side (your messages)
        bubble_x = width - bubble_width - margin
        bubble_color = (97, 11, 45)  # Dark pink/magenta
        text_color = (255, 220, 236)  # Light pink
        name_y = height // 2 - bubble_height // 2 - 60
    else:
        # Left side (their messages)
        bubble_x = margin
        bubble_color = (45, 45, 50)  # Dark gray
        text_color = (240, 240, 240)  # White
        name_y = height // 2 - bubble_height // 2 - 60
    
    bubble_y = height // 2 - bubble_height // 2
    
    # Draw name above bubble
    draw.text((bubble_x, name_y), name, fill=text_color, font=font_name)
    
    # Draw rounded rectangle bubble
    draw.rounded_rectangle(
        [(bubble_x, bubble_y), (bubble_x + bubble_width, bubble_y + bubble_height)],
        radius=30,
        fill=bubble_color
    )
    
    # Draw text lines
    text_y = bubble_y + padding
    for line in lines:
        draw.text((bubble_x + padding, text_y), line, fill=text_color, font=font_text)
        text_y += line_height
    
    return img


def create_conversation_reel(conversation_text, output_path="reel.mp4"):
    """
    Create Instagram Reel from conversation
    
    conversation_text: Multi-line string with format:
        Name1: Text1
        Name2: Text2
        ...
    """
    
    print("🎬 Creating conversation reel...")
    
    # Parse conversation
    lines = []
    for line in conversation_text.strip().split('\n'):
        line = line.strip()
        if ':' in line and line:
            name, text = line.split(':', 1)
            lines.append((name.strip(), text.strip()))
    
    if not lines:
        print("❌ No valid conversation found")
        return None
    
    print(f"📝 Parsed {len(lines)} conversation lines")
    
    # Generate voiceover
    print("🎤 Generating voiceover...")
    generate_voiceover_sync(lines, "voiceover.mp3")
    
    # Get audio duration to calculate timing
    audio = AudioFileClip("voiceover.mp3")
    total_duration = audio.duration
    
    # Calculate duration per message (equal distribution)
    duration_per_message = total_duration / len(lines)
    
    # Create video clips for each message
    clips = []
    current_time = 0
    
    for i, (name, text) in enumerate(lines):
        print(f"🖼️  Creating frame {i+1}/{len(lines)}: {name}")
        
        # Alternate sides (sender/receiver)
        is_sender = (i % 2 == 0)
        
        # Create chat bubble frame
        frame = create_chat_bubble_frame(name, text, is_sender)
        frame.save(f"temp_frame_{i}.png")
        
        # Create clip from frame
        clip = ImageClip(f"temp_frame_{i}.png", duration=duration_per_message)
        clip = clip.with_start(current_time)
        
        clips.append(clip)
        current_time += duration_per_message
    
    # Composite video
    print("🎥 Compositing video...")
    video = CompositeVideoClip(clips, size=(1080, 1920))
    
    # Add voiceover
    video = video.with_audio(audio)
    
    # Export
    print(f"💾 Exporting reel to {output_path}...")
    video.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',
        threads=4
    )
    
    # Cleanup temp files
    for i in range(len(lines)):
        temp_file = f"temp_frame_{i}.png"
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    if os.path.exists("voiceover.mp3"):
        os.remove("voiceover.mp3")
    
    print(f"✅ Reel created successfully: {output_path}")
    return output_path


if __name__ == "__main__":
    # Test with sample conversation
    test_conversation = """
Riya: Are you awake?
Kai: Yeah. Can't sleep.
Riya: Me neither.
Kai: What's on your mind?
Riya: How everything changed.
Kai: I know what you mean.
"""
    
    create_conversation_reel(test_conversation, "test_reel.mp4")

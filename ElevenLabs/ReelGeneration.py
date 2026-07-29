"""
ReelGeneration.py

Main entry point for creating Instagram reels.
"""

from chat_parser import parse_conversation
from voice_generator import generate_voiceover
from video_generator import create_video


def create_conversation_reel(
    conversation_text,
    output_path="reel.mp4",
):
    print("🎬 Creating Reel...")

    conversation = parse_conversation(conversation_text)

    if not conversation:
        print("❌ No valid conversation found.")
        return None

    print(f"📝 {len(conversation)} messages found")

    print("🎤 Generating voiceover...")

    audio_file, durations = generate_voiceover(conversation)

    print("🎥 Creating video...")

    create_video(
        conversation=conversation,
        durations=durations,
        audio_file=audio_file,
        output_path=output_path,
    )

    print(f"\n✅ Reel saved as {output_path}")

    return output_path


if __name__ == "__main__":

    test_conversation = """
Riya: Are you awake?
Kai: Yeah. Can't sleep.
Riya: Me neither.
Kai: What's on your mind?
Riya: How everything changed.
Kai: I know what you mean.
"""

    create_conversation_reel(
        test_conversation,
        "test_reel.mp4",
    )
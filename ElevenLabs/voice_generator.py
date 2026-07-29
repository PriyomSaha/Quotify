"""
voice_generator.py

Generates expressive voiceovers using ElevenLabs.
"""

from elevenlabs.client import ElevenLabs
from moviepy import AudioFileClip, concatenate_audioclips

from config import (
    ELEVENLABS_API_KEY,
    MODEL_ID,
    TEMP_AUDIO_DIR,
    VOICEOVER_FILE,
)

from speaker import get_voice


client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


# ----------------------------------------------------
# Generate One Message
# ----------------------------------------------------

def generate_message(name: str, text: str, index: int):

    voice_id = get_voice(name)

    output_file = TEMP_AUDIO_DIR / f"{index:03}.mp3"

    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=MODEL_ID,
        text=text,
    )

    with open(output_file, "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)

    return output_file


# ----------------------------------------------------
# Merge Audio Files
# ----------------------------------------------------

def merge_audio(audio_files):

    clips = []
    durations = []

    for file in audio_files:

        clip = AudioFileClip(str(file))

        durations.append(clip.duration)

        clips.append(clip)

    final_audio = concatenate_audioclips(clips)

    final_audio.write_audiofile(
        str(VOICEOVER_FILE),
        fps=44100,
        logger=None,
    )

    final_audio.close()

    for clip in clips:
        clip.close()

    return str(VOICEOVER_FILE), durations


# ----------------------------------------------------
# Generate Full Conversation
# ----------------------------------------------------

def generate_voiceover(conversation):

    # Remove old temporary files
    for file in TEMP_AUDIO_DIR.glob("*.mp3"):
        try:
            file.unlink()
        except:
            pass

    audio_files = []

    for index, (speaker, message) in enumerate(conversation):

        print(f"🎤 {speaker}: {message}")

        audio_files.append(
            generate_message(
                speaker,
                message,
                index,
            )
        )

    return merge_audio(audio_files)
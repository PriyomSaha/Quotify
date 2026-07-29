"""
video_generator.py

Creates Instagram reel style chat videos.
"""

from moviepy import ImageClip, AudioFileClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS,
    OUTPUT_VIDEO,
    TEMP_FRAMES_DIR,
)


BASE_DIR = Path(__file__).resolve().parent


# ----------------------------------------------------
# Fonts
# ----------------------------------------------------

try:
    FONT_PATH = BASE_DIR / "Montserrat" / "static" / "Montserrat-Light.ttf"

    NAME_FONT = ImageFont.truetype(
        str(FONT_PATH),
        420
    )

    TEXT_FONT = ImageFont.truetype(
        str(FONT_PATH),
        640
    )

except Exception:

    NAME_FONT = ImageFont.load_default()
    TEXT_FONT = ImageFont.load_default()


# ----------------------------------------------------
# Create Chat Screen
# ----------------------------------------------------

def create_chat_frame(messages):

    img = Image.new(
        "RGB",
        (VIDEO_WIDTH, VIDEO_HEIGHT),
        (20, 20, 25)
    )

    draw = ImageDraw.Draw(img)


    bubble_width = 920
    padding = 45
    margin = 40
    line_height = 80


    y_position = 250


    for index, (speaker, text, sender) in enumerate(messages):

        words = text.split()

        lines = []
        current = []

        for word in words:

            current.append(word)

            test = " ".join(current)

            bbox = draw.textbbox(
                (0,0),
                test,
                font=TEXT_FONT
            )

            if bbox[2] > bubble_width - padding * 2:

                current.pop()

                if current:
                    lines.append(
                        " ".join(current)
                    )

                current = [word]


        if current:
            lines.append(
                " ".join(current)
            )


        bubble_height = (
            padding * 2
            + len(lines) * line_height
            + 80
        )


        if sender:

            bubble_x = VIDEO_WIDTH - bubble_width - margin

            bubble_color = (
                97,
                11,
                45
            )

            text_color = (
                255,
                220,
                236
            )

        else:

            bubble_x = margin

            bubble_color = (
                45,
                45,
                50
            )

            text_color = (
                240,
                240,
                240
            )


        # Speaker name

        draw.text(
            (
                bubble_x,
                y_position - 55
            ),
            speaker,
            fill=text_color,
            font=NAME_FONT
        )


        # Bubble

        draw.rounded_rectangle(
            [
                (
                    bubble_x,
                    y_position
                ),
                (
                    bubble_x + bubble_width,
                    y_position + bubble_height
                )
            ],
            radius=45,
            fill=bubble_color
        )


        text_y = y_position + padding


        for line in lines:

            draw.text(
                (
                    bubble_x + padding,
                    text_y
                ),
                line,
                fill=text_color,
                font=TEXT_FONT
            )

            text_y += line_height


        y_position += bubble_height + 90


        # Prevent overflow

        if y_position > VIDEO_HEIGHT - 300:

            break


    return img



# ----------------------------------------------------
# Create Video
# ----------------------------------------------------

def create_video(
        conversation,
        durations,
        audio_file,
        output_path=str(OUTPUT_VIDEO)
):


    clips = []

    current_time = 0

    visible_messages = []


    for index, (speaker, message) in enumerate(conversation):


        print(
            f"🖼️ Creating frame {index+1}/{len(conversation)}"
        )


        visible_messages.append(
            (
                speaker,
                message,
                index % 2 == 0
            )
        )


        frame = create_chat_frame(
            visible_messages
        )


        frame_path = (
            TEMP_FRAMES_DIR /
            f"{index:03}.png"
        )


        frame.save(frame_path)


        clip = (
            ImageClip(
                str(frame_path)
            )
            .with_duration(
                durations[index]
            )
            .with_start(
                current_time
            )
        )


        clips.append(clip)


        current_time += durations[index]


    print("🎥 Rendering video...")


    video = CompositeVideoClip(
        clips,
        size=(
            VIDEO_WIDTH,
            VIDEO_HEIGHT
        )
    )


    audio = AudioFileClip(
        audio_file
    )


    video = video.with_audio(
        audio
    )


    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4
    )


    audio.close()
    video.close()


    for file in TEMP_FRAMES_DIR.glob("*.png"):

        file.unlink()


    print(
        f"✅ Saved: {output_path}"
    )


    return output_path
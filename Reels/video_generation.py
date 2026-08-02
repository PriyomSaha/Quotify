"""
video_generation.py

Aesthetic Vibes - Professional Reel Composer

Features:

✓ 1080x1920 Reel format
✓ Slow Ken Burns cinematic zoom
✓ Dark cinematic shade layer
✓ Film grain texture
✓ Cross fade transitions
✓ Background music
✓ Voice sync
✓ Animated subtitles
✓ Instagram/Facebook ready
"""


from pathlib import Path
from typing import List
import random
import numpy as np

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    ColorClip,
    concatenate_audioclips,
    concatenate_videoclips,
)

from moviepy import vfx

from subtitle_generation import generate_subtitles

from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS,
    IMAGE_FADE,
    BITRATE,
    BACKGROUND_MUSIC,
    MUSIC_VOLUME,
    FONT,
    FONT_SIZE,
    FONT_COLOR,
    STROKE_COLOR,
    STROKE_WIDTH,
    BOTTOM_MARGIN,
)


# ============================================================
# CINEMATIC SETTINGS
# ============================================================

DARK_OVERLAY_OPACITY = 0.50
FILM_GRAIN_AMOUNT = 30
ZOOM_MIN = 1.00
ZOOM_MAX = 1.10  # Enable subtle zoom
CROSSFADE_DURATION = 0.5  # Crossfade duration in seconds


# ============================================================
# REEL COMPOSER
# ============================================================

class ReelComposer:

    def __init__(self, images: List[str], narration_audio: str, output_file: str):
        self.images = images
        self.audio_path = narration_audio
        self.output = output_file
        self.audio = AudioFileClip(narration_audio)
        self.duration = self.audio.duration
        self.image_duration = self.duration / len(images)
        self.subtitles = generate_subtitles(narration_audio)


    def create_image_clip(self, image_path: str, add_fade_in: bool = True, add_fade_out: bool = False):
        """
        Creates:
        - Image fitting
        - Slow zoom
        - Dark cinematic layer
        - Fade transitions
        """
        from moviepy.video.fx.Resize import Resize
        from moviepy.video.fx.CrossFadeIn import CrossFadeIn
        from moviepy.video.fx.CrossFadeOut import CrossFadeOut
        
        image = ImageClip(image_path)
        
        # Get original dimensions
        img_width = image.size[0]
        img_height = image.size[1]
        
        # Calculate scale to fit video dimensions
        scale_height = VIDEO_HEIGHT / img_height
        scale_width = VIDEO_WIDTH / img_width
        scale = max(scale_height, scale_width)  # Ensure image covers entire frame
        
        # Resize image to cover frame
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        image = image.with_effects([Resize(new_size=(new_width, new_height))])
        
        image = image.with_duration(self.image_duration)
        image = image.with_fps(FPS)
        
        # KEN BURNS EFFECT (Slow Zoom)
        if ZOOM_MAX > 1.0:
            zoom_amount = random.uniform(ZOOM_MIN, ZOOM_MAX)
            zoom_direction = random.choice(["in", "out"])
            
            def resize_function(t):
                progress = t / self.image_duration
                if zoom_direction == "in":
                    scale_factor = 1.0 + (zoom_amount - 1.0) * progress
                else:
                    scale_factor = zoom_amount - (zoom_amount - 1.0) * progress
                
                scaled_w = int(new_width * scale_factor)
                scaled_h = int(new_height * scale_factor)
                return (scaled_w, scaled_h)
            
            image = image.with_effects([Resize(resize_function)])
        
        image = image.with_position("center")
        
        # DARK CINEMATIC OVERLAY
        dark_layer = ColorClip(
            size=(VIDEO_WIDTH, VIDEO_HEIGHT),
            color=(0, 0, 0)
        )
        dark_layer = dark_layer.with_duration(self.image_duration)
        dark_layer = dark_layer.with_opacity(DARK_OVERLAY_OPACITY)
        
        # COMBINE IMAGE + SHADE
        combined = CompositeVideoClip(
            [image, dark_layer],
            size=(VIDEO_WIDTH, VIDEO_HEIGHT)
        )
        
        # Add fade effects
        effects = []
        if add_fade_in:
            effects.append(CrossFadeIn(CROSSFADE_DURATION))
        if add_fade_out:
            effects.append(CrossFadeOut(CROSSFADE_DURATION))
        
        if effects:
            combined = combined.with_effects(effects)
        
        return combined
        ########################################################
    # CREATE IMAGE TRACK
    ########################################################


    def create_image_track(self):
        """
        Creates image track with crossfade transitions between clips.
        Uses overlapping clips for smooth crossfades.
        """
        if not self.images:
            raise ValueError("No images provided")
        
        clips = []

        for idx, image in enumerate(self.images):
            is_first = (idx == 0)
            is_last = (idx == len(self.images) - 1)
            
            # First clip: fade in, fade out
            # Middle clips: fade out only (overlaps with next clip's fade in)
            # Last clip: no fade out
            clip = self.create_image_clip(
                image,
                add_fade_in=is_first,
                add_fade_out=not is_last
            )
            
            # Set start time with overlap for crossfade
            if idx == 0:
                start_time = 0
            else:
                start_time = idx * self.image_duration - CROSSFADE_DURATION
            
            clip = clip.with_start(start_time)
            clips.append(clip)
        
        # Calculate total duration
        total_duration = len(self.images) * self.image_duration - (len(self.images) - 1) * CROSSFADE_DURATION
        
        # Composite all clips together
        final_clip = CompositeVideoClip(
            clips,
            size=(VIDEO_WIDTH, VIDEO_HEIGHT)
        ).with_duration(total_duration)
        
        return final_clip


    ########################################################
    # FILM GRAIN EFFECT
    ########################################################

    def add_film_grain(self, clip):
        """
        Adds subtle cinematic film grain.
        """
        def make_frame(get_frame, t):
            frame = get_frame(t)
            noise = np.random.normal(0, FILM_GRAIN_AMOUNT, frame.shape)
            frame = frame.astype(np.float32) + noise
            return np.clip(frame, 0, 255).astype(np.uint8)
        
        return clip.transform(make_frame)


    ########################################################
    # CREATE SUBTITLE TRACK
    ########################################################


    def create_subtitle_track(self):


        subtitle_clips = []


        for subtitle in self.subtitles:


            text = subtitle["text"].strip()


            if not text:

                continue


            clip = TextClip(

                text=text,

                font=FONT,

                font_size=FONT_SIZE,

                color=FONT_COLOR,

                stroke_color=STROKE_COLOR,

                stroke_width=STROKE_WIDTH,

                method="caption",

                size=(

                    VIDEO_WIDTH - 120,

                    None

                ),

                text_align="center"

            )


            clip = (

                clip

                .with_start(

                    subtitle["start"]

                )

                .with_duration(

                    max(

                        0.5,

                        subtitle["end"]

                        -

                        subtitle["start"]

                    )

                )

                .with_position(

                    (

                        "center",

                        VIDEO_HEIGHT -

                        BOTTOM_MARGIN

                    )

                )

            )


            clip = clip.with_effects(

                [

                    vfx.CrossFadeIn(

                        0.12

                    ),

                    vfx.CrossFadeOut(

                        0.12

                    )

                ]

            )


            subtitle_clips.append(

                clip

            )


        return subtitle_clips


    ########################################################
    # AUDIO TRACK
    ########################################################


    def create_audio_track(self):
        """
        Creates composite audio track with narration and optional background music.
        Background music is automatically detected from inputs folder.
        """
        narration = self.audio
        audio_tracks = [narration]
        
        # Check for background music in inputs folder
        inputs_dir = Path("Reels/inputs")
        
        # Look for any audio file in inputs folder
        music_file = None
        if inputs_dir.exists():
            # Check for common audio formats
            for ext in ['*.mp3', '*.wav', '*.m4a', '*.ogg']:
                audio_files = list(inputs_dir.glob(ext))
                if audio_files:
                    music_file = audio_files[0]  # Use first found
                    break
        
        # Fallback to config path if no file found in inputs
        if not music_file and Path(BACKGROUND_MUSIC).exists():
            music_file = Path(BACKGROUND_MUSIC)
        
        if music_file and music_file.exists():
            print(f"Adding background music: {music_file.name}")
            
            music = AudioFileClip(str(music_file))
            
            # Set very low volume (from config)
            music = music.with_volume_scaled(MUSIC_VOLUME)
            
            # Loop music if shorter than narration
            if music.duration < self.duration:
                loops = int(self.duration // music.duration) + 1
                music = concatenate_audioclips([music] * loops)
            
            # Trim to match narration duration
            music = music.subclipped(0, self.duration)
            
            audio_tracks.append(music)
            print(f"Background music volume: {MUSIC_VOLUME * 100:.1f}%")
        else:
            print("No background music found (checked Reels/inputs/ folder)")
        
        return CompositeAudioClip(audio_tracks)


    ########################################################
    # FINAL VIDEO COMPOSITION
    ########################################################


    def compose(self):


        print()

        print(

            "Creating cinematic image track..."

        )


        image_track = self.create_image_track()


        print(

            "Applying film grain..."

        )


        image_track = self.add_film_grain(

            image_track

        )


        print(

            "Creating subtitles..."

        )


        subtitle_track = self.create_subtitle_track()


        print(

            "Creating audio..."

        )


        audio_track = self.create_audio_track()


        print(

            "Combining final reel..."

        )


        final_video = CompositeVideoClip(

            [

                image_track,

                *subtitle_track

            ],

            size=(

                VIDEO_WIDTH,

                VIDEO_HEIGHT

            )

        )


        final_video = final_video.with_audio(

            audio_track

        )


        Path(

            self.output

        ).parent.mkdir(

            parents=True,

            exist_ok=True

        )


        print()

        print(

            "Rendering final reel..."

        )


        final_video.write_videofile(

            self.output,

            codec="libx264",

            audio_codec="aac",

            fps=FPS,

            bitrate=BITRATE,

            preset="medium",

            threads=4

        )


        print()

        print(

            "=" * 60

        )

        print(

            "AESTHETIC VIBES REEL CREATED"

        )

        print(

            "=" * 60

        )

        print(

            self.output

        )


        return self.output

# ============================================================
# PUBLIC FUNCTION
# ============================================================


def create_reel(

    images: list[str],

    narration_audio: str,

    output_file: str

):


    composer = ReelComposer(

        images=images,

        narration_audio=narration_audio,

        output_file=output_file

    )


    return composer.compose()


# ============================================================
# STANDALONE TEST
# ============================================================


if __name__ == "__main__":
    from pathlib import Path
    import sys

    # Find the most recent output folder (handle both relative paths)
    output_base = Path("output")
    
    # If running from root, check Reels/output
    if not output_base.exists():
        output_base = Path("Reels/output")
    
    if not output_base.exists():
        print("Error: No output folder found. Run main.py first to generate content.")
        sys.exit(1)
    
    # Get all timestamp folders
    folders = sorted([f for f in output_base.iterdir() if f.is_dir() and len(f.name) == 15])
    
    if not folders:
        print("Error: No reel folders found in output/. Run main.py first.")
        sys.exit(1)
    
    # Use the most recent folder
    REEL_FOLDER = folders[-1]
    print(f"Using folder: {REEL_FOLDER}")

    image_folder = REEL_FOLDER / "images"
    narration_file = REEL_FOLDER / "voiceover.mp3"
    output_file = REEL_FOLDER / "reel.mp4"

    # Check if images exist
    if not image_folder.exists():
        print(f"Error: Images folder not found: {image_folder}")
        print(f"Available in {REEL_FOLDER}:")
        for item in REEL_FOLDER.iterdir():
            print(f"  - {item.name}")
        sys.exit(1)

    images = sorted([str(img) for img in image_folder.glob("*.png")])

    if not images:
        print(f"Error: No images found in {image_folder}")
        sys.exit(1)

    print(f"\nImages found: {len(images)}")
    for img in images:
        print(f"  {Path(img).name}")

    # Check audio
    if not narration_file.exists():
        print(f"Error: Voice file missing: {narration_file}")
        sys.exit(1)

    print(f"\nVoice: {narration_file.name}")

    # Create reel
    print(f"\nCreating reel: {output_file}\n")
    create_reel(
        images=images,
        narration_audio=str(narration_file),
        output_file=str(output_file)
    )
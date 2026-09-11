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
from typing import List, Optional
import random
import numpy as np
import tempfile
import textwrap
import sys

from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    ColorClip,
    VideoClip,
    concatenate_audioclips,
    concatenate_videoclips,
)

from moviepy import vfx
from PIL import Image, ImageDraw, ImageFont

from .subtitle_generation import generate_subtitles

from .config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS,
    DARK_OVERLAY_OPACITY,
    BITRATE,
    BACKGROUND_MUSIC,
    MUSIC_VOLUME,
    FONT,
    FONT_SIZE,
    FONT_COLOR,
    STROKE_COLOR,
    STROKE_WIDTH,
    BOTTOM_MARGIN,
    TOP_MARGIN,
    LOGO_FONT,
    LOGO_FONT_COLOR,
    LOGO_TEXT,
    LOGO_FONT_SIZE,
    SUBTITLE_AUDIO_DELAY,
    # Cinematic effects
    ZOOM_MIN,
    ZOOM_MAX,
    FILM_GRAIN_AMOUNT,
    CROSSFADE_DURATION,
    END_CARD_DURATION,
    SUBTITLE_MIN_DURATION,
    SUBTITLE_HOLD_TIME,
    SUBTITLE_FADE,
    SUBTITLE_MAX_WIDTH_OFFSET,
    SUBTITLE_PADDING,
    SUBTITLE_LINE_SPACING,
    END_CARD_BG_COLOR,
    PROFILE_PIC_SIZE,
    PROFILE_FADE_IN,
    WATERMARK_IMG_HEIGHT,
    WATERMARK_OPACITY,
    WATERMARK_GLOW_ALPHA,
    WATERMARK_TEXT_ALPHA,
    WATERMARK_GLOW_BLUR_RADIUS,
)

# ============================================================
# CINEMATIC SETTINGS
# ============================================================


# ============================================================
# REEL COMPOSER
# ============================================================

class ReelComposer:

    def __init__(self, images: List[str], narration_audio: str, output_file: str, hook_line: Optional[str] = None):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Initializing ReelComposer...")
            self.images = images
            self.audio_path = narration_audio
            self.output = output_file
            self.hook_line = (hook_line or "").strip()
            self.audio_delay = float(SUBTITLE_AUDIO_DELAY or 0.0)
            
            logger.info(f"Loading audio file: {narration_audio}")
            self.audio = AudioFileClip(narration_audio)
            self.duration = self.audio.duration
            logger.info(f"Audio duration: {self.duration:.2f} seconds")
            
            # Account for crossfade overlaps so the scene images end exactly when narration ends.
            # Without this, the image track becomes shorter than narration and the end card appears
            # while the voiceover is still speaking.
            self.image_duration = (
                self.duration + (len(images) - 1) * CROSSFADE_DURATION
            ) / len(images)
            logger.info(f"Image duration: {self.image_duration:.2f} seconds each")
            
            logger.info("Generating subtitles with Whisper base model...")
            self.subtitles = generate_subtitles(narration_audio)
            logger.info(f"✅ Generated {len(self.subtitles)} subtitle segments")
            
        except Exception as e:
            logger.error(f"❌ ReelComposer initialization failed: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise


    def create_image_clip(self, image_path: str, add_fade_in: bool = True, add_fade_out: bool = False, duration=None):
        """
        Creates:
        - Image fitting
        - Slow zoom
        - Dark cinematic layer
        - Fade transitions

        duration: optional override (first clip holds longer for the
        hook-only cold open before narration begins).
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

        clip_duration = float(duration) if duration else self.image_duration
        image = image.with_duration(clip_duration)
        image = image.with_fps(FPS)

        # KEN BURNS EFFECT (Slow Zoom)
        if ZOOM_MAX > 1.0:
            zoom_amount = random.uniform(ZOOM_MIN, ZOOM_MAX)
            zoom_direction = random.choice(["in", "out"])

            def resize_function(t):
                progress = t / clip_duration
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
        dark_layer = dark_layer.with_duration(clip_duration)
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
        watermark_clips = []  # Store watermarks separately

        # Cold open: the hook shows alone for the first `audio_delay` seconds
        # (no narration, no subtitles). The first image holds through the hook,
        # every later scene shifts by the same delay so narration, subtitles
        # and visuals all start together at t = audio_delay.
        delay = self.audio_delay

        for idx, image in enumerate(self.images):
            is_first = (idx == 0)
            is_last = (idx == len(self.images) - 1)

            # First clip: NO fade in (starts immediately), fade out
            # Middle clips: fade out only (overlaps with next clip's fade in)
            # Last clip: no fade out
            clip = self.create_image_clip(
                image,
                add_fade_in=False,  # No fade-in for first image
                add_fade_out=not is_last,
                # First image holds longer so the hook plays over it silently
                duration=(self.image_duration + delay) if is_first else None
            )
            
            # Set start time with overlap for crossfade
            if idx == 0:
                start_time = 0
            else:
                start_time = idx * self.image_duration - CROSSFADE_DURATION + delay
            
            clip = clip.with_start(start_time)
            clips.append(clip)
            
            # Create watermark for this image (syncs with image fades)
            watermark = self.create_watermark_for_image(
                start_time=start_time,
                duration=self.image_duration + (delay if is_first else 0),
                add_fade_out=not is_last  # Fade out when image fades out
            )
            watermark_clips.append(watermark)
        
        # Calculate total duration (visuals cover the hook hold + narration)
        total_duration = delay + len(self.images) * self.image_duration - (len(self.images) - 1) * CROSSFADE_DURATION
        
        # Composite all clips together
        final_clip = CompositeVideoClip(
            clips,
            size=(VIDEO_WIDTH, VIDEO_HEIGHT)
        ).with_duration(total_duration)
        
        # Store watermarks for later composition
        self.watermark_clips = watermark_clips
        
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
        """
        Creates animated subtitle track with extended visibility.
        Subtitles stay visible longer for better readability.
        """
        subtitle_clips = []

        # If a pinned hook overlay is showing the same text at the top for the
        # first ~1.8s, don't ALSO render that sentence as the opening subtitle
        # (avoids the "double/overlapping subtitle" on the first frame).
        hook_text = (getattr(self, "hook_line", "") or "").strip().lower()

        def _same_as_hook(text: str) -> bool:
            if not hook_text:
                return False
            t = text.strip().lower()
            return t == hook_text or t.endswith(hook_text) or hook_text.endswith(t)

        for i, subtitle in enumerate(self.subtitles):
            text = subtitle["text"].strip()

            if not text:
                continue

            if _same_as_hook(text):
                continue

            start_time = subtitle["start"] + self.audio_delay
            end_time = subtitle["end"] + self.audio_delay
            
            # Calculate extended duration for better readability
            base_duration = end_time - start_time
            
            # Minimum visible time (comfortable reading speed)
            min_duration = SUBTITLE_MIN_DURATION
            
            # Add hold time: keep subtitle visible after speech ends
            hold_time = SUBTITLE_HOLD_TIME
            
            # Calculate extended duration
            extended_duration = max(min_duration, base_duration + hold_time)
            
            # Check if next subtitle exists to avoid overlap
            if i + 1 < len(self.subtitles):
                next_start = self.subtitles[i + 1]["start"] + self.audio_delay
                # Don't overlap into next subtitle's start time
                max_duration = next_start - start_time
                duration = min(extended_duration, max_duration)
            else:
                # Last subtitle - use extended duration
                duration = extended_duration

            clip = self._create_standard_subtitle(
                    text,
                    start_time,
                    duration
                )

            subtitle_clips.append(clip)

        return subtitle_clips

    def _create_standard_subtitle(self, text, start_time, duration):

        image_path = self._render_subtitle_image(text)

        clip = (
            ImageClip(image_path)
            .with_start(start_time)
            .with_duration(duration)
            .with_position(
                (
                    "center",
                    TOP_MARGIN,
                )
            )
            .with_effects(
                [
                    vfx.CrossFadeIn(SUBTITLE_FADE),
                    vfx.CrossFadeOut(SUBTITLE_FADE),
                ]
            )
        )

        return clip

    def _render_subtitle_image(self, text):
        """
        Renders subtitle using Pillow and returns the path to a temporary PNG.
        """

        max_width = VIDEO_WIDTH - SUBTITLE_MAX_WIDTH_OFFSET
        padding = SUBTITLE_PADDING
        line_spacing = SUBTITLE_LINE_SPACING

        font = ImageFont.truetype(FONT, FONT_SIZE)

        dummy = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy)

        # -----------------------------
        # Word wrapping
        # -----------------------------
        words = text.split()
        lines = []
        current = ""

        for word in words:
            test = word if current == "" else current + " " + word

            bbox = draw.textbbox(
                (0, 0),
                test,
                font=font,
                stroke_width=STROKE_WIDTH,
            )

            width = bbox[2] - bbox[0]

            if width <= max_width:
                current = test
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        # -----------------------------
        # Calculate image size
        # -----------------------------
        line_heights = []

        max_line_width = 0

        for line in lines:
            bbox = draw.textbbox(
                (0, 0),
                line,
                font=font,
                stroke_width=STROKE_WIDTH,
            )

            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            max_line_width = max(max_line_width, w)
            line_heights.append(h)

        text_height = (
            sum(line_heights)
            + line_spacing * (len(lines) - 1)
        )

        img_w = int(max_line_width + padding * 2)
        img_h = int(text_height + padding * 2)

        img = Image.new(
            "RGBA",
            (img_w, img_h),
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(img)

        y = padding

        for i, line in enumerate(lines):

            draw.text(
                (padding, y),
                line,
                font=font,
                fill=FONT_COLOR,
                stroke_width=STROKE_WIDTH,
                stroke_fill=STROKE_COLOR,
            )

            y += line_heights[i] + line_spacing

        temp = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        )

        img.save(temp.name)

        return temp.name


    def _render_hook_image(self, text):
        """
        Renders the pinned hook line as a transparent PNG (top-third overlay).
        """
        font_size = int(FONT_SIZE * 1.25)
        max_width = VIDEO_WIDTH - int(VIDEO_WIDTH * 0.10)
        padding = SUBTITLE_PADDING * 2
        line_spacing = SUBTITLE_LINE_SPACING + 8

        font = ImageFont.truetype(FONT, font_size)

        dummy = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy)

        words = text.split()
        lines = []
        current = ""

        for word in words:
            test = word if current == "" else current + " " + word
            bbox = draw.textbbox((0, 0), test, font=font, stroke_width=STROKE_WIDTH)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current = test
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        # Measure
        line_heights = []
        max_line_width = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=STROKE_WIDTH)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            max_line_width = max(max_line_width, w)
            line_heights.append(h)

        text_height = sum(line_heights) + line_spacing * (len(lines) - 1)
        img_w = int(max_line_width + padding * 2)
        img_h = int(text_height + padding * 2)

        img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Soft dark backing for readability over any image
        draw.rounded_rectangle(
            (0, 0, img_w - 1, img_h - 1),
            radius=24,
            fill=(0, 0, 0, 140),
        )

        y = padding
        for i, line in enumerate(lines):
            draw.text(
                (padding, y),
                line,
                font=font,
                fill=FONT_COLOR,
                stroke_width=STROKE_WIDTH + 1,
                stroke_fill=STROKE_COLOR,
            )
            y += line_heights[i] + line_spacing

        temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(temp.name)
        return temp.name

    def create_hook_overlay(self):
        """
        Returns an ImageClip with the pinned hook line shown ALONE at the
        start (cold open): first `audio_delay` seconds (default 3.0s) with
        no narration and no subtitles, positioned in the exact vertical
        middle of the frame. It fades out right as narration begins.
        Returns None when no hook_line exists.
        """
        hook = getattr(self, "hook_line", "") or ""
        hook = hook.strip()
        if not hook:
            return None

        image_path = self._render_hook_image(hook)

        # Center the hook vertically using the real rendered size. The
        # narration text sits at TOP_MARGIN (upper area); the middle of the
        # frame is well below it, so the two can't overlap.
        with Image.open(image_path) as _img:
            _hook_w, _hook_h = _img.size
        hook_y = max(int((VIDEO_HEIGHT - _hook_h) // 2), 0)

        # Hook owns the whole cold open; it fades out exactly when the
        # narration voice + subtitles begin.
        hook_duration = float(self.audio_delay) if self.audio_delay > 0 else 1.8

        clip = (
            ImageClip(image_path)
            .with_start(0)
            .with_duration(hook_duration)
            .with_position(("center", hook_y))
            .with_effects([
                vfx.CrossFadeIn(0.15),
                vfx.CrossFadeOut(0.4),
            ])
        )
        return clip

    def create_end_card(self, duration=END_CARD_DURATION):
        """
        Creates an end card with profile picture.
        Shows for the black screen duration at the end.
        """
        # Check for profile picture in parent folder
        profile_pic_path = Path("ProfilePic.jpg")
        
        # Also check in Reels parent folder
        if not profile_pic_path.exists():
            profile_pic_path = Path("Reels") / ".." / "ProfilePic.jpg"
        
        if not profile_pic_path.exists():
            # If no profile pic, return black screen
            return ColorClip(
                size=(VIDEO_WIDTH, VIDEO_HEIGHT),
                color=(0, 0, 0)
            ).with_duration(duration)
        
        print(f"Adding end card with profile picture: {profile_pic_path}")
        
        # Load profile picture
        from moviepy.video.fx.Resize import Resize
        profile_clip = ImageClip(str(profile_pic_path))
        
        # Resize to fit nicely (e.g., 400x400 circle in center)
        profile_size = PROFILE_PIC_SIZE
        profile_clip = profile_clip.with_effects([
            Resize(new_size=(profile_size, profile_size))
        ])
        
        # Create dark background
        background = ColorClip(
            size=(VIDEO_WIDTH, VIDEO_HEIGHT),
            color=END_CARD_BG_COLOR  # Dark blue-grey
        ).with_duration(duration)
        
        # Position profile pic in center
        profile_clip = profile_clip.with_duration(duration)
        profile_clip = profile_clip.with_position("center")
        
        # Add fade in effect
        profile_clip = profile_clip.with_effects([vfx.CrossFadeIn(PROFILE_FADE_IN)])
        
        # Composite background + profile pic
        end_card = CompositeVideoClip(
            [background, profile_clip],
            size=(VIDEO_WIDTH, VIDEO_HEIGHT)
        ).with_duration(duration)
        
        return end_card

    def create_watermark_for_image(self, start_time, duration, add_fade_out=False):
        """
        Creates a watermark that syncs with image transitions.
        Fades out when the image fades out.
        """
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        import tempfile
        
        
        
        
        # Create larger image for glow effect
        img_width = VIDEO_WIDTH
        img_height = WATERMARK_IMG_HEIGHT
        
        # Create transparent image
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        
        # Load font
        try:
            font = ImageFont.truetype(LOGO_FONT, LOGO_FONT_SIZE)  # Use Permanent Marker font
        except:
            font = ImageFont.load_default()
        
        # Get text dimensions
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), LOGO_TEXT, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center position
        text_x = (img_width - text_width) // 2
        text_y = (img_height - text_height) // 2
        
        # Create glow layer
        glow_img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_img)
        
        # Draw glow (will be blurred)
        glow_color_alpha = (*LOGO_FONT_COLOR, WATERMARK_GLOW_ALPHA)
        glow_draw.text((text_x, text_y), LOGO_TEXT, font=font, fill=glow_color_alpha)
        
        # Apply Gaussian blur for glow effect
        glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=WATERMARK_GLOW_BLUR_RADIUS))
        
        # Draw main text on original image
        text_color_alpha = (*LOGO_FONT_COLOR, WATERMARK_TEXT_ALPHA)
        draw.text((text_x, text_y), LOGO_TEXT, font=font, fill=text_color_alpha)
        
        # Composite glow and text
        final_img = Image.alpha_composite(glow_img, img)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        final_img.save(temp_file.name)
        
        # Create ImageClip from watermark
        watermark_clip = ImageClip(temp_file.name)
        watermark_clip = watermark_clip.with_duration(duration)
        watermark_clip = watermark_clip.with_start(start_time)
        
        # Position toward bottom (mirrors the former top placement)
        y_position = VIDEO_HEIGHT - img_height - BOTTOM_MARGIN
        watermark_clip = watermark_clip.with_position((0, y_position))
        
        watermark_clip = watermark_clip.with_opacity(WATERMARK_OPACITY)
        
        # Add fade out effect if needed (syncs with image fade)
        if add_fade_out:
            watermark_clip = watermark_clip.with_effects([vfx.CrossFadeOut(CROSSFADE_DURATION)])
        
        return watermark_clip

    ########################################################
    # AUDIO TRACK
    ########################################################


    def create_audio_track(self, total_duration=None):
        """
        Creates composite audio track with narration and optional background music.
        Background music is automatically detected from inputs folder.

        Narration stays at its original length. Background music can continue
        beyond narration for the end-card/profile-template section.
        """
        narration = self.audio
        # Cold open: narration stays silent for the first `audio_delay`
        # seconds (the hook plays alone), then the voice starts.
        if self.audio_delay > 0:
            narration = narration.with_start(self.audio_delay)
        audio_tracks = [narration]
        target_duration = total_duration or self.duration
        
        # Check for background music in inputs folder
        inputs_dir = Path("Reels/inputs")
        
        # Look for all available audio files in inputs folder and choose one randomly.
        music_file = None
        if inputs_dir.exists():
            audio_files = []
            for ext in ["*.mp3", "*.wav", "*.m4a", "*.ogg"]:
                audio_files.extend(inputs_dir.glob(ext))

            audio_files = sorted(audio_files)
            if audio_files:
                music_file = random.choice(audio_files)
                print(
                    "Available background music: "
                    + ", ".join(file.name for file in audio_files)
                )
        
        # Fallback to config path if no file found in inputs
        if not music_file and Path(BACKGROUND_MUSIC).exists():
            music_file = Path(BACKGROUND_MUSIC)
        
        if music_file and music_file.exists():
            print(f"Adding random background music: {music_file.name}")
            
            music = AudioFileClip(str(music_file))
            
            # Set very low volume (from config)
            music = music.with_volume_scaled(MUSIC_VOLUME)
            
            # Loop music if shorter than the full video duration.
            if music.duration < target_duration:
                loops = int(target_duration // music.duration) + 1
                music = concatenate_audioclips([music] * loops)
            
            # Trim to match the full video duration, including the end card.
            music = music.subclipped(0, target_duration)
            
            audio_tracks.append(music)
            print(f"Background music volume: {MUSIC_VOLUME * 100:.1f}%")
        else:
            print("No background music found (checked Reels/inputs/ folder)")
        
        return CompositeAudioClip(audio_tracks)


    ########################################################
    # FINAL VIDEO COMPOSITION
    ########################################################


    def compose(self):
        import logging
        import psutil
        import os
        
        logger = logging.getLogger(__name__)
        
        # Log memory usage at start
        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            logger.info(f"💾 Memory at composition start: {mem_info.rss / 1024 / 1024:.1f} MB")
        except:
            pass  # psutil might not be available

        print()
        print("Creating cinematic image track...")
        image_track = self.create_image_track()

        # Only apply film grain if not on Render (memory intensive)
        import os
        from .config import FILM_GRAIN_INTENSITY
        
        if FILM_GRAIN_INTENSITY > 0:
            print("Applying film grain...")
            image_track = self.add_film_grain(image_track)
        else:
            print("Skipping film grain (disabled for performance)...")

        print("Creating subtitles...")
        subtitle_track = self.create_subtitle_track()

        # Cold-open hook overlay (audio_delay seconds) keeps the first 3s strong
        hook_clip = self.create_hook_overlay()

        # Make sure the story visuals run through the hook hold + narration.
        # The profile template/end card should appear only after this point.
        expected_visual_end = self.audio_delay + self.duration
        if abs(image_track.duration - expected_visual_end) > 0.05:
            image_track = image_track.with_duration(expected_visual_end)

        print(f"Adding profile end card after narration ({END_CARD_DURATION:.1f}s)...")
        end_card = self.create_end_card(duration=END_CARD_DURATION)
        image_track = concatenate_videoclips(
            [image_track, end_card],
            method="compose"
        )
        final_video_duration = expected_visual_end + END_CARD_DURATION

        print("Creating audio...")
        audio_track = self.create_audio_track(total_duration=final_video_duration)
        
        # Create watermark (synced with image transitions)
        print("Adding watermarks synced with images...")
        watermark_clips = getattr(self, 'watermark_clips', [])

        print("Combining final reel...")
        
        # Composite layers
        composite_clips = [image_track]
        
        # Add synced watermarks
        if watermark_clips:
            composite_clips.extend(watermark_clips)
        
        # Add subtitles on top
        composite_clips.extend(subtitle_track)

        # Add cold-open hook overlay on top (audio_delay seconds)
        if hook_clip is not None:
            composite_clips.append(hook_clip)
        
        final_video = CompositeVideoClip(
            composite_clips,
            size=(VIDEO_WIDTH, VIDEO_HEIGHT)
        )

        final_video = final_video.with_audio(audio_track)


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
        
        threads = 4
        preset = "medium"
        
        logger.info(f"Video settings: {VIDEO_WIDTH}x{VIDEO_HEIGHT} @ {FPS}fps, bitrate={BITRATE}")
        logger.info(f"Render preset: {preset}, threads: {threads}")
        logger.info("⏳ Starting video encoding (this takes 2-4 minutes on Render)...")
        sys.stdout.flush()


        final_video.write_videofile(

            self.output,

            codec="libx264",

            audio_codec="aac",

            fps=FPS,

            bitrate=BITRATE,

            preset=preset,

            threads=threads,
            
            logger="bar"  # Show progress bar for visibility

        )
        
        logger.info("✅ Video encoding complete!")
        sys.stdout.flush()


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

    output_file: str,

    hook_line: Optional[str] = None

):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Creating reel with {len(images)} images")
        logger.info(f"Audio: {narration_audio}")
        logger.info(f"Output: {output_file}")
        
        composer = ReelComposer(
            images=images,
            narration_audio=narration_audio,
            output_file=output_file,
            hook_line=hook_line
        )
        
        logger.info("ReelComposer initialized, starting composition...")
        result = composer.compose()
        logger.info(f"✅ Reel composition completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ create_reel() failed: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

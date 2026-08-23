# ============================================================
# STANDALONE TEST
# ============================================================

import sys
from pathlib import Path

# Make sure the project root is importable no matter where this file
# is executed from, so `Reels.video_generation` resolves as a package
# and its relative imports (`.config`, `.subtitle_generation`) work.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from Reels.video_generation import create_reel


if __name__ == "__main__":
    REEL_FOLDER = Path("Reels/output/20260823_233418")

    image_folder = REEL_FOLDER / "images"
    voiceover = REEL_FOLDER / "voiceover.mp3"
    output_file = REEL_FOLDER / "reel.mp4"

    images = sorted(str(p) for p in image_folder.glob("*.png"))

    if not images:
        raise ValueError(f"No images found in {image_folder}")

    if not voiceover.exists():
        raise FileNotFoundError(f"Voiceover not found: {voiceover}")

    create_reel(
        images=images,
        narration_audio=str(voiceover),
        output_file=str(output_file),
    )
    print(f"\n✅ Reel created: {output_file}")
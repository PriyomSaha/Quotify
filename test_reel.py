# ============================================================
# STANDALONE TEST
# ============================================================

import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Make sure the project root is importable no matter where this file
# is executed from, so `Reels.video_generation` resolves as a package
# and its relative imports (`.config`, `.subtitle_generation`) work.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from Reels.video_generation import create_reel
from Reels.voice_generation import generate_voice


def load_story(story_file: Path) -> Dict[str, Any]:
    """Load an existing story.json (for the --reuse-story path)."""
    with open(story_file, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    REEL_FOLDER = Path("Reels/output/20261101_130827")

    # If the reel output folder does not exist, create it so downstream
    # paths resolve cleanly.
    if not REEL_FOLDER.exists():
        print(f"⚠️  Reel folder not found, creating: {REEL_FOLDER}")
        REEL_FOLDER.mkdir(parents=True, exist_ok=True)

    image_folder = REEL_FOLDER / "images"
    voiceover = REEL_FOLDER / "voiceover.mp3"
    output_file = REEL_FOLDER / "reel.mp4"
    story_file = REEL_FOLDER / "story.json"

    # If the images folder does not exist, create it. A missing folder
    # simply yields no images, which is handled as a skip below.
    if not image_folder.exists():
        print(f"⚠️  Images folder not found, creating: {image_folder}")
        image_folder.mkdir(parents=True, exist_ok=True)

    images = sorted(str(p) for p in image_folder.glob("*.png"))

    if not images:
        print(f"⚠️  No images found in {image_folder} — skipping reel creation.")
        return

    # Generate the voiceover only when it is missing and a usable
    # story.json is available to read the narration from. Otherwise
    # skip the voice step gracefully instead of crashing.
    if not voiceover.exists():
        if not story_file.exists():
            print(
                f"⚠️  Voiceover missing and no story.json at {story_file} — "
                f"cannot generate narration, skipping reel creation."
            )
            return
        try:
            story = load_story(story_file)
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"⚠️  Could not read story.json ({exc}) — "
                f"skipping reel creation."
            )
            return
        narration = (story.get("narration") or "").strip()
        if not narration:
            print(f"⚠️  story.json has no narration — skipping reel creation.")
            return
        hook_line = (story.get("hook_line") or "").strip() or None
        print(f"🎙️  Generating voiceover -> {voiceover}")
        generate_voice(
            text=narration,
            output_file=str(voiceover),
            voice=story.get("voice") or None,
        )

    # Read the hook line from story.json so the cold-open hook overlay
    # (first 1.5s, centered) is rendered exactly like a Reels_main run.
    hook_line = None
    if story_file.exists():
        try:
            hook_line = (
                json.loads(story_file.read_text(encoding="utf-8"))
                .get("hook_line")
                or ""
            ).strip() or None
        except (OSError, json.JSONDecodeError):
            hook_line = None

    print(f"Hook line: {hook_line or '(none found in story.json)'}")

    if not voiceover.exists():
        print(f"⚠️  Voiceover not found: {voiceover} — skipping reel creation.")
        return

    create_reel(
        images=images,
        narration_audio=str(voiceover),
        output_file=str(output_file),
        hook_line=hook_line,
    )
    print(f"\n✅ Reel created: {output_file}")


if __name__ == "__main__":
    main()
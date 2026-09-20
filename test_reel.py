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


if __name__ == "__main__":
    REEL_FOLDER = Path("Reels/output/20260920_153341")

    image_folder = REEL_FOLDER / "images"
    voiceover = REEL_FOLDER / "voiceover.mp3"
    output_file = REEL_FOLDER / "reel.mp4"
    story_file = REEL_FOLDER / "story.json"
    images = sorted(str(p) for p in image_folder.glob("*.png"))

    if not images:
        raise ValueError(f"No images found in {image_folder}")

    if not voiceover.exists():
        story = load_story(story_file)
        narration = (story.get("narration") or "").strip()
        hook_line = (story.get("hook_line") or "").strip() or None
        generate_voice(
            text=narration,
            output_file=str(voiceover),
            voice=story.get("voice") or None,
        )
        raise FileNotFoundError(f"Voiceover not found: {voiceover}")

    # Read the hook line from story.json so the cold-open hook overlay
    # (first 1.5s, centered) is rendered exactly like a Reels_main run.
    hook_line = None
    if story_file.exists():
        hook_line = (
            json.loads(story_file.read_text(encoding="utf-8"))
            .get("hook_line")
            or ""
        ).strip() or None

    print(f"Hook line: {hook_line or '(none found in story.json)'}")

    create_reel(
        images=images,
        narration_audio=str(voiceover),
        output_file=str(output_file),
        hook_line=hook_line,
    )
    print(f"\n✅ Reel created: {output_file}")
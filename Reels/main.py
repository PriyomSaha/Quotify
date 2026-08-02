from datetime import datetime
import json
import sys
from pathlib import Path

from config import OUTPUT_DIR
from image_generation import generate_images_for_reel
from story_generation import generate_story
from video_generation import create_reel
from voice_generation import generate_voice


def load_existing_story(story_path: str):
    """
    Load an existing story JSON file.
    """
    path = Path(story_path)
    if not path.exists():
        raise FileNotFoundError(f"Story file not found: {story_path}")
    
    with open(path, "r", encoding="utf8") as f:
        return json.load(f)


def get_timestamp_from_story_path(story_path: Path) -> str:
    """
    Extract timestamp from story path.
    If story is at output/20260801_230959/story.json, return '20260801_230959'
    If story is at output/20260801_230959.json (old format), return '20260801_230959'
    """
    # Check if parent directory is a timestamp
    parent_name = story_path.parent.name
    if parent_name != "output" and len(parent_name) == 15:  # timestamp format YYYYMMDD_HHMMSS
        return parent_name
    
    # Otherwise use the filename stem
    return story_path.stem


if __name__ == "__main__":
    # Parse command line arguments
    use_existing_story = len(sys.argv) > 1 and sys.argv[1].endswith('.json')
    images_only = '--images-only' in sys.argv
    
    if use_existing_story:
        story_path = Path(sys.argv[1])
        print(f"📖 Loading existing story from: {story_path}\n")
        story = load_existing_story(str(story_path))
        
        # Extract timestamp from path
        timestamp = get_timestamp_from_story_path(story_path)
        
        # Use the story's directory
        if story_path.parent.name != "output":
            # Story is in output/timestamp/ structure
            output_folder = story_path.parent
        else:
            # Story is in output/ (old format), create timestamp folder
            output_folder = OUTPUT_DIR / timestamp
            output_folder.mkdir(exist_ok=True)
        
        story_file = output_folder / "story.json"
    else:
        # Generate new story with new timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder = OUTPUT_DIR / timestamp
        output_folder.mkdir(parents=True, exist_ok=True)
        
        print("📝 Step 1 : Generating Story...\n")
        story = generate_story()
        story_file = output_folder / "story.json"
    
    # Define paths within the output folder
    image_dir = output_folder / "images"
    audio_path = output_folder / "voiceover.mp3"
    video_file = output_folder / "reel.mp4"
    
    # Generate images
    print("🎨 Step 2 : Generating Images...\n")
    images = generate_images_for_reel(
        reel_json=story,
        output_dir=image_dir,
        prefix="scene"
    )
    
    # If images-only mode, stop here
    if images_only:
        print("\n✅ Image Generation Completed (images-only mode)")
        print(f"📁 Story : {story_file}")
        print(f"🖼️  Images: {image_dir}")
        sys.exit(0)
    
    # Generate voice
    print("🎤 Step 3 : Voice Generation...\n")
    generate_voice(
        text=story["narration"],
        output_file=str(audio_path)
    )
    
    # Save story (both for new and existing, to ensure it's in right location)
    print("📄 Saving Story...\n")
    with open(
        story_file,
        "w",
        encoding="utf8"
    ) as f:
        json.dump(
            story,
            f,
            indent=4,
            ensure_ascii=False
        )
    
    # Create video
    print("🎬 Step 4 : Composing Reel...\n")
    create_reel(
        images=images,
        narration_audio=str(audio_path),
        output_file=str(video_file)
    )
    
    print("\n✅ Reel Generation Completed")
    print(f"📁 Output Folder: {output_folder}")
    print(f"📄 Story : {story_file}")
    print(f"🖼️  Images: {image_dir}")
    print(f"🎤 Audio : {audio_path}")
    print(f"🎬 Video : {video_file}")
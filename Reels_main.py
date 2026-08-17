from datetime import datetime
import json
import sys
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List

# Change these from relative to absolute imports
from Reels.config import OUTPUT_DIR, AUTO_UPLOAD_REELS
from Reels.image_generation import generate_images_for_reel
from Reels.story_generation import generate_story
from Reels.video_generation import create_reel
from Reels.voice_generation import generate_voice
from Reels.hashtag_generation import build_reel_caption
from event_detector import CONTENT_REEL, get_today_event


def load_existing_story(story_path: str) -> Dict[str, Any]:
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



def upload_to_social_media(video_file: Path, caption: str, output_dir: Path) -> Dict[str, Any]:
    """
    Upload video to Facebook and Instagram using the shared uploader.
    """
    from Reels.social_upload import upload_reel_to_social_media

    print("\n📤 Step 5/5: Uploading to social media...")
    print(f"Caption length: {len(caption)} chars")
    print(f"Caption preview: {caption[:500]}")
    sys.stdout.flush()

    return upload_reel_to_social_media(
        video_file=video_file,
        caption=caption,
        output_dir=output_dir,
        require_facebook=True,
        require_instagram=True,
    )


def generate_complete_reel(story_path: Optional[str] = None, images_only: bool = False, upload: Optional[bool] = None) -> Dict[str, Any]:
    """
    Generate a complete reel from scratch or using existing story.
    
    Args:
        story_path: Path to existing story JSON (optional)
        images_only: If True, only generate images and stop
        upload: If True, upload to Facebook and Instagram
                If None, reads from AUTO_UPLOAD_REELS env variable (default behavior)
    
    Returns:
        dict: Paths to generated files and upload results
    """
    
    event = get_today_event(content_type=CONTENT_REEL)

    # Determine upload behavior
    # Priority: explicit parameter > environment variable > default (True)
    if upload is None:
        upload = AUTO_UPLOAD_REELS
        print(f"📤 Upload setting from config: {upload}")
    
    output_folder: Path
    story_file: Path
    story: Dict[str, Any]
    
    if story_path:
        story_path_obj = Path(story_path)
        print(f"📖 Loading existing story from: {story_path_obj}\n")
        story = load_existing_story(story_path)
        
        # Extract timestamp from path
        timestamp = get_timestamp_from_story_path(story_path_obj)
        
        # Use the story's directory
        if story_path_obj.parent.name != "output":
            # Story is in output/timestamp/ structure
            output_folder = story_path_obj.parent
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
    images: List[str] = generate_images_for_reel(
        reel_json=story,
        output_dir=image_dir,
        prefix="scene"
    )
    
    # If images-only mode, stop here
    if images_only:
        print("\n✅ Image Generation Completed (images-only mode)")
        print(f"📁 Story : {story_file}")
        print(f"🖼️  Images: {image_dir}")
        return {
            "output_folder": str(output_folder),
            "story_file": str(story_file),
            "image_dir": str(image_dir),
            "images": images
        }
    
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
    
    result = {
        "output_folder": str(output_folder),
        "story_file": str(story_file),
        "image_dir": str(image_dir),
        "audio_file": str(audio_path),
        "video_file": str(video_file),
        "images": images,
        "story": story
    }
    
    # Upload to social media if enabled
    if upload:
        caption = build_reel_caption(
            title=story.get("title", ""),
            fallback_text=story.get("narration", "")[:100],
            event=event,
        )
        upload_results = upload_to_social_media(video_file, caption, output_folder)
        result["upload_results"] = upload_results
        
        print("\n🎉 Reel Pipeline Completed!")
        print(f"📦 Facebook: {upload_results.get('facebook', 'N/A')}")
        print(f"📱 Instagram: {upload_results.get('instagram', 'N/A')}")
        
        # Clean up local files after confirmed successful upload
        if upload_results.get("success"):
            print(f"\n🗑️ Deleting output folder: {output_folder}")
            shutil.rmtree(output_folder)
            print("✅ Output folder deleted")
    
    return result


if __name__ == "__main__":
    # Parse command line arguments.
    # For event-date testing, set EVENT_TEST_DATE in .env instead of passing --test-date.
    args = sys.argv[1:]
    use_existing_story = len(args) > 0 and args[0].endswith('.json')
    images_only = '--images-only' in args
    no_upload = '--no-upload' in args
    
    story_path_arg: Optional[str] = args[0] if use_existing_story else None
    
    # Determine upload parameter
    # Command line --no-upload flag overrides env variable
    upload_param = False if no_upload else None  # None = use config default
    
    # Call the main function
    generate_complete_reel(
        story_path=story_path_arg, 
        images_only=images_only,
        upload=upload_param
    )
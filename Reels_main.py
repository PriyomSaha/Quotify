from datetime import datetime
import json
import sys
import os
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Change these from relative to absolute imports
from Reels.config import OUTPUT_DIR, AUTO_UPLOAD_REELS
from Reels.image_generation import generate_images_for_reel
from Reels.story_generation import generate_story
from Reels.video_generation import create_reel
from Reels.voice_generation import generate_voice


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
    Upload video to Facebook and Instagram.
    Returns upload results.
    """
    import requests
    
    print("\n📤 Step 5/5: Uploading to social media...")
    print(f"Caption: {caption[:50]}...")
    sys.stdout.flush()
    
    # Get environment variables
    PAGE_ID = os.getenv("PAGE_ID")
    PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
    API_VERSION = os.getenv("API_VERSION", "v21.0")
    IG_USER_ID = os.getenv("IG_USER_ID")
    
    if not all([PAGE_ID, PAGE_ACCESS_TOKEN, IG_USER_ID]):
        print("❌ Missing required environment variables for upload")
        print(f"PAGE_ID: {'✓' if PAGE_ID else '✗'}")
        print(f"PAGE_ACCESS_TOKEN: {'✓' if PAGE_ACCESS_TOKEN else '✗'}")
        print(f"IG_USER_ID: {'✓' if IG_USER_ID else '✗'}")
        return {"facebook": None, "instagram": None}
    
    results = {
        "facebook": None,
        "instagram": None,
        "cloudinary_url": None
    }
    
    # Step 5a: Upload to Cloudinary for Instagram
    print("\n📤 Step 5a: Uploading video to Cloudinary...")
    sys.stdout.flush()
    
    cloudinary_url = None
    cloudinary_public_id = None
    delete_video_from_cloudinary = None
    
    try:
        from Reels.cloudinary_uploader import upload_video_to_cloudinary, delete_video_from_cloudinary
        
        cloudinary_result = upload_video_to_cloudinary(
            video_path=str(video_file),
            folder="instagram_reels",
            public_id=f"reel_{output_dir.name}"
        )
        
        cloudinary_url = cloudinary_result["secure_url"]
        cloudinary_public_id = cloudinary_result["public_id"]
        results["cloudinary_url"] = cloudinary_url
        
        print(f"✅ Video uploaded to Cloudinary")
        print(f"🔗 URL: {cloudinary_url[:80]}...")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"❌ Cloudinary upload failed: {e}")
        import traceback
        print(traceback.format_exc())
    
    # Step 5b: Upload to Facebook
    print("\n📤 Step 5b: Uploading video to Facebook...")
    sys.stdout.flush()
    
    fb_url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/videos"
    
    try:
        with open(str(video_file), "rb") as video:
            fb_response = requests.post(
                fb_url,
                files={"source": video},
                data={
                    "description": caption,
                    "published": "true",
                    "access_token": PAGE_ACCESS_TOKEN,
                },
                timeout=300,
            )
            
            fb_result = fb_response.json()
            fb_video_id = fb_result.get("id")
            results["facebook"] = fb_video_id
            
            if fb_video_id:
                print(f"✅ Facebook video uploaded: {fb_video_id}")
            else:
                print(f"❌ Facebook upload failed: {fb_result}")
            sys.stdout.flush()
                
    except Exception as e:
        print(f"❌ Facebook upload failed: {e}")
        import traceback
        print(traceback.format_exc())
        sys.stdout.flush()
    
    # Step 5c: Upload to Instagram
    if not cloudinary_url:
        print("❌ Cannot post to Instagram without Cloudinary URL")
        print("⚠️ Facebook upload completed, Instagram skipped")
        sys.stdout.flush()
        return results
    
    print("\n📱 Step 5c: Publishing to Instagram as Reel...")
    sys.stdout.flush()
    
    # Create media container
    container_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media"
    container_res = requests.post(
        container_url,
        data={
            "video_url": cloudinary_url,
            "caption": caption,
            "media_type": "REELS",
            "access_token": PAGE_ACCESS_TOKEN,
        },
    ).json()
    
    creation_id = container_res.get("id")
    
    if not creation_id:
        print(f"❌ IG Container creation failed: {container_res}")
        error_message = container_res.get("error", {}).get("message", "Unknown error")
        print(f"Error details: {error_message}")
        sys.stdout.flush()
        return results
    
    print(f"✅ IG Container created: {creation_id}")
    sys.stdout.flush()
    
    # Poll container status
    print("⏳ Polling container status (30-90 seconds)...")
    sys.stdout.flush()
    
    max_attempts = 30
    container_ready = False
    
    for attempt in range(1, max_attempts + 1):
        time.sleep(3)
        
        status_url = f"https://graph.facebook.com/{API_VERSION}/{creation_id}"
        status_res = requests.get(
            status_url,
            params={
                "fields": "status_code",
                "access_token": PAGE_ACCESS_TOKEN,
            }
        )
        
        status_data = status_res.json()
        status_code = status_data.get("status_code", "UNKNOWN")
        
        print(f"Attempt {attempt}/{max_attempts}: Status = {status_code}")
        sys.stdout.flush()
        
        if status_code == "FINISHED":
            container_ready = True
            print("✅ Container ready for publishing!")
            sys.stdout.flush()
            break
        elif status_code in ["ERROR", "EXPIRED", "PUBLISHED"]:
            print(f"❌ Container status invalid: {status_code}")
            sys.stdout.flush()
            return results
    
    if not container_ready:
        print(f"❌ Container not ready after {max_attempts * 3} seconds")
        sys.stdout.flush()
        return results
    
    # Publish the reel
    print("Publishing Instagram Reel...")
    sys.stdout.flush()
    
    publish_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media_publish"
    publish_res = requests.post(
        publish_url,
        data={
            "creation_id": creation_id,
            "access_token": PAGE_ACCESS_TOKEN,
        },
    ).json()
    
    ig_post_id = publish_res.get("id", "")
    results["instagram"] = ig_post_id
    
    if ig_post_id:
        print(f"✅ Instagram Reel published: {ig_post_id}")
        
        # Delete from Cloudinary after successful post
        if cloudinary_public_id and delete_video_from_cloudinary:
            print("🗑️ Deleting video from Cloudinary...")
            try:
                delete_video_from_cloudinary(cloudinary_public_id)
                print("✅ Cloudinary video deleted")
            except Exception as e:
                print(f"⚠️ Failed to delete from Cloudinary: {e}")
        sys.stdout.flush()
    else:
        print(f"⚠️ Instagram publish failed: {publish_res}")
        sys.stdout.flush()
    
    return results


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
        caption = story.get("title", story.get("narration", "")[:100])[:2000]
        upload_results = upload_to_social_media(video_file, caption, output_folder)
        result["upload_results"] = upload_results
        
        print("\n🎉 Reel Pipeline Completed!")
        print(f"📦 Facebook: {upload_results.get('facebook', 'N/A')}")
        print(f"📱 Instagram: {upload_results.get('instagram', 'N/A')}")
        
        # Clean up local files after successful upload
        if upload_results.get("facebook") or upload_results.get("instagram"):
            print(f"\n🗑️ Deleting output folder: {output_folder}")
            shutil.rmtree(output_folder)
            print("✅ Output folder deleted")
    
    return result


if __name__ == "__main__":
    # Parse command line arguments
    use_existing_story = len(sys.argv) > 1 and sys.argv[1].endswith('.json')
    images_only = '--images-only' in sys.argv
    no_upload = '--no-upload' in sys.argv
    
    story_path_arg: Optional[str] = sys.argv[1] if use_existing_story else None
    
    # Determine upload parameter
    # Command line --no-upload flag overrides env variable
    upload_param = False if no_upload else None  # None = use config default
    
    # Call the main function
    generate_complete_reel(
        story_path=story_path_arg, 
        images_only=images_only,
        upload=upload_param
    )
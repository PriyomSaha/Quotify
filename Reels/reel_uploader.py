"""
Reel Uploader

Complete implementation for uploading video reels to Facebook and Instagram.
Uses Meta Graph API for both platforms.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

from .exceptions import (
    VideoNotFoundError,
    FacebookUploadError,
    InstagramUploadError,
    VideoNotAccessibleError,
    ContainerPollingError,
    PublishError,
)
from .utils import (
    get_timestamp_from_path,
    validate_video_exists,
    wait_for_public_video,
    poll_instagram_container,
    format_response,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
PAGE_ID = os.getenv("PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
API_VERSION = os.getenv("API_VERSION", "v21.0")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")

# Constants
FACEBOOK_TIMEOUT = 300  # 5 minutes for video upload
INSTAGRAM_CONTAINER_TIMEOUT = 120  # 2 minutes for container processing
VIDEO_ACCESSIBILITY_TIMEOUT = 60  # 1 minute to wait for public URL


def get_public_video_url(video_path: str) -> str:
    """
    Generate public URL for video file.
    
    Args:
        video_path: Local path to video (e.g., "output/20260803_153500/reel.mp4")
        
    Returns:
        Public URL (e.g., "https://domain.com/reels/20260803_153500/reel.mp4")
        
    Raises:
        ValueError: If PUBLIC_BASE_URL is not configured
    """
    if not PUBLIC_BASE_URL:
        raise ValueError(
            "PUBLIC_BASE_URL environment variable is not set. "
            "Required for Instagram reel upload."
        )
    
    timestamp = get_timestamp_from_path(video_path)
    public_url = f"{PUBLIC_BASE_URL.rstrip('/')}/reels/{timestamp}/reel.mp4"
    
    logger.info(f"Generated public URL: {public_url}")
    return public_url


def upload_facebook_reel(
    video_path: str,
    caption: str = ""
) -> str:
    """
    Upload video reel to Facebook Page.
    
    Uses the Graph API video endpoint which supports both regular videos and reels.
    
    Args:
        video_path: Path to MP4 video file
        caption: Optional caption/description for the reel
        
    Returns:
        Facebook video ID
        
    Raises:
        VideoNotFoundError: If video file doesn't exist
        FacebookUploadError: If upload fails
    """
    logger.info("=" * 60)
    logger.info("FACEBOOK REEL UPLOAD")
    logger.info("=" * 60)
    
    # Validate video exists
    video_file = validate_video_exists(video_path)
    
    # Verify credentials
    if not PAGE_ID or not PAGE_ACCESS_TOKEN:
        raise FacebookUploadError(
            "Missing Facebook credentials. "
            "Ensure PAGE_ID and PAGE_ACCESS_TOKEN are set."
        )
    
    # Build API endpoint for Facebook Page videos
    # This endpoint handles both regular videos and reels
    url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/videos"
    
    logger.info(f"Uploading to Facebook: {url}")
    logger.info(f"Video: {video_path} ({video_file.stat().st_size / (1024*1024):.2f} MB)")
    
    try:
        # Open video file in binary mode
        with open(video_file, "rb") as video:
            
            # Prepare form data
            files = {"source": video}
            data = {
                "description": caption,
                "published": "true",  # Publish immediately
                "access_token": PAGE_ACCESS_TOKEN,
            }
            
            # Upload video
            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=FACEBOOK_TIMEOUT
            )
            
            # Log response
            logger.info(f"Facebook response status: {response.status_code}")
            logger.debug(f"Facebook response: {response.text}")
            
            # Parse response
            result = response.json()
            
            # Check for errors
            if response.status_code != 200:
                error_message = result.get("error", {}).get("message", "Unknown error")
                error_code = result.get("error", {}).get("code", "")
                
                raise FacebookUploadError(
                    f"Facebook upload failed: {error_message} (code: {error_code})",
                    status_code=response.status_code,
                    response=result
                )
            
            # Extract video ID
            video_id = result.get("id")
            
            if not video_id:
                raise FacebookUploadError(
                    f"No video ID in Facebook response: {result}",
                    response=result
                )
            
            logger.info(f"✓ Facebook reel uploaded successfully")
            logger.info(f"  Video ID: {video_id}")
            
            return video_id
            
    except requests.RequestException as e:
        raise FacebookUploadError(
            f"Network error during Facebook upload: {str(e)}"
        )


def post_instagram_reel(
    video_url: str,
    caption: str = ""
) -> Dict[str, Any]:
    """
    Post reel to Instagram using public video URL.
    
    This is a two-step process:
    1. Create media container with video URL
    2. Poll until container is ready
    3. Publish container
    
    Args:
        video_url: Public URL to MP4 video file
        caption: Optional caption for the reel
        
    Returns:
        Instagram API response with media ID
        
    Raises:
        InstagramUploadError: If any step fails
        VideoNotAccessibleError: If video URL is not accessible
        ContainerPollingError: If container processing fails
        PublishError: If final publish step fails
    """
    logger.info("=" * 60)
    logger.info("INSTAGRAM REEL UPLOAD")
    logger.info("=" * 60)
    
    # Verify credentials
    if not IG_USER_ID or not PAGE_ACCESS_TOKEN:
        raise InstagramUploadError(
            "Missing Instagram credentials. "
            "Ensure IG_USER_ID and PAGE_ACCESS_TOKEN are set."
        )
    
    # Step 1: Verify video is publicly accessible
    logger.info("Step 1: Verifying video accessibility...")
    wait_for_public_video(
        video_url,
        timeout=VIDEO_ACCESSIBILITY_TIMEOUT
    )
    
    # Step 2: Create Instagram media container
    logger.info("Step 2: Creating Instagram media container...")
    
    container_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media"
    
    container_data = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": PAGE_ACCESS_TOKEN,
        "share_to_feed": "true",  # Share reel to main feed
    }
    
    try:
        container_response = requests.post(
            container_url,
            data=container_data,
            timeout=30
        )
        
        logger.info(f"Container creation status: {container_response.status_code}")
        logger.debug(f"Container response: {container_response.text}")
        
        container_result = container_response.json()
        
        # Check for errors
        if container_response.status_code != 200:
            error_message = container_result.get("error", {}).get("message", "Unknown error")
            error_code = container_result.get("error", {}).get("code", "")
            
            raise InstagramUploadError(
                f"Instagram container creation failed: {error_message} (code: {error_code})",
                status_code=container_response.status_code,
                response=container_result
            )
        
        # Extract container ID
        container_id = container_result.get("id")
        
        if not container_id:
            raise InstagramUploadError(
                f"No container ID in Instagram response: {container_result}",
                response=container_result
            )
        
        logger.info(f"✓ Container created: {container_id}")
        
    except requests.RequestException as e:
        raise InstagramUploadError(
            f"Network error during container creation: {str(e)}"
        )
    
    # Step 3: Poll container until ready
    logger.info("Step 3: Polling container status...")
    
    poll_instagram_container(
        container_id=container_id,
        access_token=PAGE_ACCESS_TOKEN,
        api_version=API_VERSION,
        max_wait=INSTAGRAM_CONTAINER_TIMEOUT
    )
    
    # Step 4: Publish container
    logger.info("Step 4: Publishing reel...")
    
    publish_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media_publish"
    
    publish_data = {
        "creation_id": container_id,
        "access_token": PAGE_ACCESS_TOKEN,
    }
    
    try:
        publish_response = requests.post(
            publish_url,
            data=publish_data,
            timeout=30
        )
        
        logger.info(f"Publish status: {publish_response.status_code}")
        logger.debug(f"Publish response: {publish_response.text}")
        
        publish_result = publish_response.json()
        
        # Check for errors
        if publish_response.status_code != 200:
            error_message = publish_result.get("error", {}).get("message", "Unknown error")
            error_code = publish_result.get("error", {}).get("code", "")
            
            raise PublishError(
                f"Instagram publish failed: {error_message} (code: {error_code})",
                status_code=publish_response.status_code,
                response=publish_result
            )
        
        # Extract media ID
        media_id = publish_result.get("id")
        
        if not media_id:
            raise PublishError(
                f"No media ID in publish response: {publish_result}",
                response=publish_result
            )
        
        logger.info(f"✓ Instagram reel published successfully")
        logger.info(f"  Media ID: {media_id}")
        
        return publish_result
        
    except requests.RequestException as e:
        raise PublishError(
            f"Network error during publish: {str(e)}"
        )


def post_reel_to_fb_and_instagram(
    video_path: str,
    caption: str = ""
) -> Dict[str, Any]:
    """
    Complete pipeline: Upload reel to Facebook and Instagram.
    
    This function orchestrates the entire upload process:
    1. Validates video file exists
    2. Uploads to Facebook
    3. Generates public URL
    4. Waits for URL to be accessible
    5. Creates Instagram container
    6. Polls until container is ready
    7. Publishes to Instagram
    
    Args:
        video_path: Path to MP4 video file (e.g., "output/20260803_153500/reel.mp4")
        caption: Optional caption for both platforms
        
    Returns:
        Dictionary containing:
        - status: "success"
        - facebook_video_id: Facebook video ID
        - instagram_media_id: Instagram media ID
        - video_url: Public video URL
        - facebook_response: Full Facebook API response
        - instagram_response: Full Instagram API response
        
    Raises:
        VideoNotFoundError: If video doesn't exist
        FacebookUploadError: If Facebook upload fails
        InstagramUploadError: If Instagram upload fails
        VideoNotAccessibleError: If public URL is not accessible
    """
    logger.info("\n" + "=" * 60)
    logger.info("REEL UPLOAD PIPELINE STARTED")
    logger.info("=" * 60)
    logger.info(f"Video: {video_path}")
    logger.info(f"Caption: {caption[:50]}..." if len(caption) > 50 else f"Caption: {caption}")
    logger.info("=" * 60 + "\n")
    
    # Track results
    facebook_video_id = None
    facebook_response = None
    instagram_media_id = None
    instagram_response = None
    video_url = None
    
    try:
        # Step 1: Validate video
        validate_video_exists(video_path)
        
        # Step 2: Upload to Facebook
        facebook_video_id = upload_facebook_reel(video_path, caption)
        facebook_response = {"id": facebook_video_id}
        
        # Step 3: Generate public URL
        video_url = get_public_video_url(video_path)
        
        # Step 4: Upload to Instagram (includes verification and polling)
        instagram_response = post_instagram_reel(video_url, caption)
        instagram_media_id = instagram_response.get("id")
        
        # Step 5: Format and return response
        result = format_response(
            facebook_video_id=facebook_video_id,
            instagram_media_id=instagram_media_id,
            video_url=video_url,
            facebook_response=facebook_response,
            instagram_response=instagram_response
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ REEL UPLOAD PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Facebook Video ID: {facebook_video_id}")
        logger.info(f"Instagram Media ID: {instagram_media_id}")
        logger.info(f"Public URL: {video_url}")
        logger.info("=" * 60 + "\n")
        
        return result
        
    except Exception as e:
        logger.error("\n" + "=" * 60)
        logger.error("✗ REEL UPLOAD PIPELINE FAILED")
        logger.error("=" * 60)
        logger.error(f"Error: {type(e).__name__}: {str(e)}")
        logger.error(f"Facebook uploaded: {'Yes' if facebook_video_id else 'No'}")
        logger.error(f"Instagram uploaded: {'Yes' if instagram_media_id else 'No'}")
        logger.error("=" * 60 + "\n")
        raise


# ============================================================
# MAIN - Example Usage
# ============================================================

if __name__ == "__main__":
    import json
    from typing import Union
    
    # Example usage
    video_path = "output/20260803_153500/reel.mp4"
    caption = "Test Reel - Aesthetic Vibes"
    
    try:
        result = post_reel_to_fb_and_instagram(
            video_path=video_path,
            caption=caption
        )
        
        print("\n" + "=" * 60)
        print("UPLOAD RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}")
        print(f"  {str(e)}\n")
        
        # Type-safe response access
        error_with_response: Union[
            FacebookUploadError,
            InstagramUploadError,
            PublishError
        ] = e  # type: ignore
        
        if hasattr(error_with_response, 'response') and error_with_response.response:
            print("API Response:")
            print(json.dumps(error_with_response.response, indent=2))

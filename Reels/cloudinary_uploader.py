"""
cloudinary_uploader.py

Upload videos to Cloudinary for Instagram reel posting.
Instagram requires a publicly accessible URL, Cloudinary provides this.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Cloudinary configuration
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Configure cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)


def upload_video_to_cloudinary(
    video_path: str,
    folder: str = "instagram_reels",
    public_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload video to Cloudinary and return the secure URL.
    
    Args:
        video_path: Path to the video file
        folder: Cloudinary folder (default: instagram_reels)
        public_id: Custom public ID (optional, auto-generated if not provided)
    
    Returns:
        dict with:
            - secure_url: Public HTTPS URL
            - public_id: Cloudinary public ID
            - resource_type: 'video'
            - format: File format (mp4, etc)
            - duration: Video duration in seconds
            - bytes: File size in bytes
    
    Raises:
        FileNotFoundError: If video file doesn't exist
        Exception: If upload fails
    """
    video_file = Path(video_path)
    
    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Generate public_id from filename if not provided
    if not public_id:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        public_id = f"reel_{timestamp}"
    
    logger.info(f"📤 Uploading video to Cloudinary...")
    logger.info(f"File: {video_file.name} ({video_file.stat().st_size / 1024 / 1024:.2f} MB)")
    logger.info(f"Folder: {folder}")
    logger.info(f"Public ID: {public_id}")
    
    try:
        # Upload video with optimized settings
        upload_result = cloudinary.uploader.upload(
            video_path,
            resource_type="video",
            folder=folder,
            public_id=public_id,
            overwrite=True,
            invalidate=True,  # Invalidate CDN cache
            # Video optimization settings
            eager=[
                {
                    "format": "mp4",
                    "video_codec": "h264",
                    "quality": "auto:good"
                }
            ],
            eager_async=False,  # Wait for eager transformation
            timeout=300  # 5 minute timeout for large files
        )
        
        secure_url = upload_result.get("secure_url")
        
        logger.info(f"✅ Video uploaded successfully!")
        logger.info(f"🔗 URL: {secure_url}")
        logger.info(f"⏱️ Duration: {upload_result.get('duration', 0):.1f}s")
        logger.info(f"📦 Size: {upload_result.get('bytes', 0) / 1024 / 1024:.2f} MB")
        
        return {
            "secure_url": secure_url,
            "public_id": upload_result.get("public_id"),
            "resource_type": upload_result.get("resource_type"),
            "format": upload_result.get("format"),
            "duration": upload_result.get("duration"),
            "bytes": upload_result.get("bytes"),
            "width": upload_result.get("width"),
            "height": upload_result.get("height"),
            "created_at": upload_result.get("created_at")
        }
        
    except Exception as e:
        logger.error(f"❌ Cloudinary upload failed: {type(e).__name__}: {str(e)}")
        raise


def delete_video_from_cloudinary(public_id: str) -> bool:
    """
    Delete video from Cloudinary after successful Instagram post.
    
    Args:
        public_id: Cloudinary public ID (e.g., 'instagram_reels/reel_20260803_152145')
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        logger.info(f"🗑️ Deleting video from Cloudinary: {public_id}")
        
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type="video",
            invalidate=True
        )
        
        if result.get("result") == "ok":
            logger.info(f"✅ Video deleted successfully")
            return True
        else:
            logger.warning(f"⚠️ Delete returned: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to delete video: {type(e).__name__}: {str(e)}")
        return False


def get_video_info(public_id: str) -> Optional[Dict[str, Any]]:
    """
    Get video information from Cloudinary.
    
    Args:
        public_id: Cloudinary public ID
    
    Returns:
        dict with video metadata or None if not found
    """
    try:
        result = cloudinary.api.resource(
            public_id,
            resource_type="video"
        )
        
        return {
            "secure_url": result.get("secure_url"),
            "format": result.get("format"),
            "duration": result.get("duration"),
            "bytes": result.get("bytes"),
            "width": result.get("width"),
            "height": result.get("height"),
            "created_at": result.get("created_at")
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get video info: {e}")
        return None


def verify_credentials() -> bool:
    """
    Verify Cloudinary credentials are configured correctly.
    
    Returns:
        bool: True if credentials are valid
    """
    if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
        logger.error("❌ Cloudinary credentials not configured")
        logger.error("Missing env vars: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET")
        return False
    
    try:
        # Test API access with a simple ping
        cloudinary.api.ping()
        logger.info("✅ Cloudinary credentials verified")
        return True
    except Exception as e:
        logger.error(f"❌ Cloudinary credentials invalid: {e}")
        return False


# Test function
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Verify credentials
    if not verify_credentials():
        sys.exit(1)
    
    # Test upload (if video path provided)
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        
        try:
            # Upload
            result = upload_video_to_cloudinary(video_path)
            print(f"\n✅ Upload successful!")
            print(f"Secure URL: {result['secure_url']}")
            print(f"Public ID: {result['public_id']}")
            
            # Get info
            info = get_video_info(result['public_id'])
            if info:
                print(f"\n📊 Video Info:")
                print(f"Duration: {info['duration']:.1f}s")
                print(f"Size: {info['bytes'] / 1024 / 1024:.2f} MB")
            else:
                print(f"\n⚠️ Could not retrieve video info")
            
            # Test delete (uncomment to actually delete)
            # delete_video_from_cloudinary(result['public_id'])
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            sys.exit(1)
    else:
        print("\n✅ Cloudinary credentials verified!")
        print("\nUsage: python cloudinary_uploader.py <video_path>")

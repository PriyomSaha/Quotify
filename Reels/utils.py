"""
Utility functions for reel upload operations.
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional
import requests

from .exceptions import VideoNotFoundError, VideoNotAccessibleError

logger = logging.getLogger(__name__)


def get_timestamp_from_path(video_path: str) -> str:
    """
    Extract timestamp from video path.
    
    Args:
        video_path: Path like "output/20260803_153500/reel.mp4"
        
    Returns:
        Timestamp string like "20260803_153500"
        
    Raises:
        ValueError: If timestamp cannot be extracted
    """
    path = Path(video_path)
    
    # Get parent directory name (should be timestamp)
    timestamp = path.parent.name
    
    # Validate timestamp format (YYYYMMDD_HHMMSS)
    if len(timestamp) == 15 and '_' in timestamp:
        date_part, time_part = timestamp.split('_')
        if len(date_part) == 8 and len(time_part) == 6:
            if date_part.isdigit() and time_part.isdigit():
                return timestamp
    
    raise ValueError(f"Could not extract valid timestamp from path: {video_path}")


def validate_video_exists(video_path: str) -> Path:
    """
    Validate that video file exists and is readable.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Path object pointing to validated video
        
    Raises:
        VideoNotFoundError: If video does not exist or is not a file
    """
    path = Path(video_path)
    
    if not path.exists():
        raise VideoNotFoundError(f"Video file does not exist: {video_path}")
    
    if not path.is_file():
        raise VideoNotFoundError(f"Path is not a file: {video_path}")
    
    if path.suffix.lower() != '.mp4':
        logger.warning(f"Video file extension is not .mp4: {video_path}")
    
    logger.info(f"✓ Video validated: {video_path} ({path.stat().st_size} bytes)")
    
    return path


def wait_for_public_video(
    video_url: str,
    timeout: int = 60,
    retry_interval: int = 2
) -> bool:
    """
    Wait for public video URL to become accessible.
    
    Polls the URL until it returns HTTP 200 or timeout is reached.
    
    Args:
        video_url: Public URL to video
        timeout: Maximum wait time in seconds (default: 60)
        retry_interval: Seconds between retries (default: 2)
        
    Returns:
        True if video is accessible
        
    Raises:
        VideoNotAccessibleError: If video is not accessible after timeout
    """
    logger.info(f"Waiting for video to be publicly accessible: {video_url}")
    
    start_time = time.time()
    attempt = 0
    
    while (time.time() - start_time) < timeout:
        attempt += 1
        
        try:
            response = requests.head(video_url, timeout=5)
            
            if response.status_code == 200:
                elapsed = time.time() - start_time
                logger.info(f"✓ Video accessible after {elapsed:.1f}s (attempt {attempt})")
                return True
            
            logger.debug(f"Attempt {attempt}: HTTP {response.status_code}")
            
        except requests.RequestException as e:
            logger.debug(f"Attempt {attempt}: {type(e).__name__}: {e}")
        
        time.sleep(retry_interval)
    
    elapsed = time.time() - start_time
    raise VideoNotAccessibleError(
        f"Video not accessible after {elapsed:.1f}s ({attempt} attempts): {video_url}"
    )


def poll_instagram_container(
    container_id: str,
    access_token: str,
    api_version: str,
    max_wait: int = 120,
    poll_interval: int = 3
) -> dict:
    """
    Poll Instagram media container until status is FINISHED.
    
    Args:
        container_id: Instagram container ID
        access_token: Page access token
        api_version: Graph API version
        max_wait: Maximum wait time in seconds (default: 120)
        poll_interval: Seconds between polls (default: 3)
        
    Returns:
        Container status response dict
        
    Raises:
        ContainerPollingError: If container processing fails or times out
    """
    from .exceptions import ContainerPollingError
    
    logger.info(f"Polling Instagram container: {container_id}")
    
    url = f"https://graph.facebook.com/{api_version}/{container_id}"
    params = {
        "fields": "status_code,status",
        "access_token": access_token
    }
    
    start_time = time.time()
    attempt = 0
    
    while (time.time() - start_time) < max_wait:
        attempt += 1
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            status_code = data.get("status_code")
            status = data.get("status")
            
            logger.debug(f"Poll {attempt}: status_code={status_code}, status={status}")
            
            # Check for FINISHED status
            if status_code == "FINISHED":
                elapsed = time.time() - start_time
                logger.info(f"✓ Container ready after {elapsed:.1f}s (poll {attempt})")
                return data
            
            # Check for error status
            if status_code == "ERROR":
                raise ContainerPollingError(
                    f"Container processing failed with ERROR status: {data}"
                )
            
            # Continue polling for IN_PROGRESS or PUBLISHED
            if status_code not in ["IN_PROGRESS", "PUBLISHED"]:
                logger.warning(f"Unexpected status_code: {status_code}")
            
        except requests.RequestException as e:
            logger.warning(f"Poll {attempt} request failed: {e}")
        
        time.sleep(poll_interval)
    
    elapsed = time.time() - start_time
    raise ContainerPollingError(
        f"Container polling timed out after {elapsed:.1f}s ({attempt} attempts). "
        f"Container may still be processing."
    )


def format_response(
    facebook_video_id: Optional[str],
    instagram_media_id: Optional[str],
    video_url: str,
    facebook_response: Optional[dict],
    instagram_response: Optional[dict]
) -> dict:
    """
    Format final response dictionary.
    
    Args:
        facebook_video_id: Facebook video ID
        instagram_media_id: Instagram media ID
        video_url: Public video URL
        facebook_response: Full Facebook API response
        instagram_response: Full Instagram API response
        
    Returns:
        Formatted response dictionary
    """
    return {
        "status": "success",
        "facebook_video_id": facebook_video_id,
        "instagram_media_id": instagram_media_id,
        "video_url": video_url,
        "facebook_response": facebook_response,
        "instagram_response": instagram_response
    }

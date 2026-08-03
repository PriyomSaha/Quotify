"""
Reels Upload Module

Handles uploading video reels to Facebook and Instagram via Meta Graph API.
Completely separate from the existing photo upload implementation.
"""

from .reel_uploader import (
    upload_facebook_reel,
    post_instagram_reel,
    post_reel_to_fb_and_instagram,
    get_public_video_url,
)

__all__ = [
    "upload_facebook_reel",
    "post_instagram_reel", 
    "post_reel_to_fb_and_instagram",
    "get_public_video_url",
]

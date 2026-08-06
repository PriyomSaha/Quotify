"""
social_upload.py

Shared reel upload helper for Facebook, Instagram, and Cloudinary.
Used by both Reels_main.py and api.py so upload behavior stays consistent.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import requests


LogFunc = Callable[[str], None]


def _default_log(message: str) -> None:
    print(message)


def upload_reel_to_social_media(
    video_file: str | Path,
    caption: str,
    output_dir: str | Path,
    *,
    require_facebook: bool = True,
    require_instagram: bool = True,
    delete_cloudinary_after_publish: bool = True,
    log: Optional[LogFunc] = None,
) -> Dict[str, Any]:
    """
    Upload a reel video to Facebook and Instagram.

    Returns a structured result. The caller should mark scheduler slots complete
    only when result["success"] is True.
    """
    log = log or _default_log
    video_path = Path(video_file)
    output_path = Path(output_dir)

    results: Dict[str, Any] = {
        "success": False,
        "facebook": None,
        "instagram": None,
        "cloudinary_url": None,
        "cloudinary_public_id": None,
        "errors": [],
    }

    if not video_path.exists():
        error = f"Video file not found: {video_path}"
        results["errors"].append(error)
        log(f"❌ {error}")
        return results

    page_id = os.getenv("PAGE_ID")
    page_access_token = os.getenv("PAGE_ACCESS_TOKEN")
    api_version = os.getenv("API_VERSION", "v21.0")
    ig_user_id = os.getenv("IG_USER_ID")

    missing = [
        name
        for name, value in {
            "PAGE_ID": page_id,
            "PAGE_ACCESS_TOKEN": page_access_token,
            "IG_USER_ID": ig_user_id,
        }.items()
        if not value
    ]

    if missing:
        error = f"Missing required upload environment variables: {', '.join(missing)}"
        results["errors"].append(error)
        log(f"❌ {error}")
        return results

    cloudinary_url = None
    cloudinary_public_id = None
    delete_video_from_cloudinary = None

    # 1. Cloudinary upload for Instagram public video URL
    log("📤 Step 5a: Uploading video to Cloudinary...")
    try:
        from Reels.cloudinary_uploader import (
            delete_video_from_cloudinary,
            upload_video_to_cloudinary,
        )

        cloudinary_result = upload_video_to_cloudinary(
            video_path=str(video_path),
            folder="instagram_reels",
            public_id=f"reel_{output_path.name}",
        )
        cloudinary_url = cloudinary_result["secure_url"]
        cloudinary_public_id = cloudinary_result["public_id"]
        results["cloudinary_url"] = cloudinary_url
        results["cloudinary_public_id"] = cloudinary_public_id
        log("✅ Video uploaded to Cloudinary")
        log(f"🔗 Public URL: {cloudinary_url[:80]}...")
    except Exception as exc:
        error = f"Cloudinary upload failed: {exc}"
        results["errors"].append(error)
        log(f"❌ {error}")

    # 2. Facebook upload
    log("📤 Step 5b: Uploading video to Facebook...")
    try:
        fb_url = f"https://graph.facebook.com/{api_version}/{page_id}/videos"
        with video_path.open("rb") as video:
            fb_response = requests.post(
                fb_url,
                files={"source": video},
                data={
                    "description": caption,
                    "published": "true",
                    "access_token": page_access_token,
                },
                timeout=300,
            )

        fb_result = fb_response.json()
        fb_video_id = fb_result.get("id")
        results["facebook"] = fb_video_id

        if fb_video_id:
            log(f"✅ Facebook video uploaded: {fb_video_id}")
        else:
            error = f"Facebook upload failed: {fb_result}"
            results["errors"].append(error)
            log(f"❌ {error}")
    except Exception as exc:
        error = f"Facebook upload request failed: {exc}"
        results["errors"].append(error)
        log(f"❌ {error}")

    # 3. Instagram Reel upload
    if not cloudinary_url:
        error = "Cannot post to Instagram without Cloudinary URL"
        results["errors"].append(error)
        log(f"❌ {error}")
    else:
        log("📱 Step 5c: Publishing to Instagram as Reel...")
        try:
            container_url = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media"
            container_res = requests.post(
                container_url,
                data={
                    "video_url": cloudinary_url,
                    "caption": caption,
                    "media_type": "REELS",
                    "access_token": page_access_token,
                },
                timeout=60,
            ).json()

            creation_id = container_res.get("id")
            if not creation_id:
                error = f"IG container creation failed: {container_res}"
                results["errors"].append(error)
                log(f"❌ {error}")
            else:
                log(f"✅ IG container created: {creation_id}")
                log("⏳ Polling container status (30-90 seconds)...")

                container_ready = False
                status_code = "UNKNOWN"
                for attempt in range(1, 31):
                    time.sleep(3)
                    status_url = f"https://graph.facebook.com/{api_version}/{creation_id}"
                    status_res = requests.get(
                        status_url,
                        params={
                            "fields": "status_code",
                            "access_token": page_access_token,
                        },
                        timeout=30,
                    )
                    status_data = status_res.json()
                    status_code = status_data.get("status_code", "UNKNOWN")
                    log(f"Attempt {attempt}/30: Status = {status_code}")

                    if status_code == "FINISHED":
                        container_ready = True
                        log("✅ Container ready for publishing")
                        break

                    if status_code in {"ERROR", "EXPIRED", "PUBLISHED"}:
                        error = f"IG container status invalid: {status_data}"
                        results["errors"].append(error)
                        log(f"❌ {error}")
                        break

                if not container_ready:
                    error = f"IG container not ready. Final status: {status_code}"
                    results["errors"].append(error)
                    log(f"❌ {error}")
                else:
                    publish_url = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media_publish"
                    publish_res = requests.post(
                        publish_url,
                        data={
                            "creation_id": creation_id,
                            "access_token": page_access_token,
                        },
                        timeout=60,
                    ).json()

                    ig_post_id = publish_res.get("id", "")
                    results["instagram"] = ig_post_id

                    if ig_post_id:
                        log(f"✅ Instagram Reel published: {ig_post_id}")
                    else:
                        error = f"Instagram publish failed: {publish_res}"
                        results["errors"].append(error)
                        log(f"❌ {error}")
        except Exception as exc:
            error = f"Instagram upload failed: {exc}"
            results["errors"].append(error)
            log(f"❌ {error}")

    if results["instagram"] and cloudinary_public_id and delete_cloudinary_after_publish:
        log("🗑️ Deleting video from Cloudinary...")
        try:
            if delete_video_from_cloudinary:
                delete_video_from_cloudinary(cloudinary_public_id)
                log("✅ Cloudinary video deleted")
        except Exception as exc:
            log(f"⚠️ Failed to delete Cloudinary video: {exc}")

    facebook_ok = bool(results["facebook"]) or not require_facebook
    instagram_ok = bool(results["instagram"]) or not require_instagram
    results["success"] = facebook_ok and instagram_ok

    if results["success"]:
        log("🎉 Social upload completed successfully")
    else:
        log("❌ Social upload did not meet success requirements")

    return results

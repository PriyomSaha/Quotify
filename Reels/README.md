# Reels Upload Module

Complete implementation for uploading video reels to Facebook and Instagram via Meta Graph API.

**IMPORTANT:** This module is completely independent of the existing photo upload implementation and does not modify or affect the existing photo upload flow.

---

## 📁 Project Structure

```
reels/
├── __init__.py           # Module exports
├── reel_uploader.py      # Main upload pipeline
├── utils.py              # Helper functions (polling, validation, etc.)
├── exceptions.py         # Custom exceptions
└── README.md            # This file
```

---

## 🚀 Quick Start

### 1. Environment Variables

Add to your `.env` file:

```env
# Existing variables (reused)
PAGE_ID=your_facebook_page_id
PAGE_ACCESS_TOKEN=your_page_access_token
IG_USER_ID=your_instagram_user_id
API_VERSION=v21.0

# New variable (required for Instagram)
PUBLIC_BASE_URL=https://your-app.onrender.com
```

**Local Testing:**
```env
# Use Cloudflare Tunnel or ngrok for local testing
PUBLIC_BASE_URL=https://xxxx.trycloudflare.com
```

**Production:**
```env
PUBLIC_BASE_URL=https://your-app.onrender.com
```

---

## 📝 Usage

### Basic Upload

```python
from reels import post_reel_to_fb_and_instagram

# Upload reel to both platforms
result = post_reel_to_fb_and_instagram(
    video_path="output/20260803_153500/reel.mp4",
    caption="Check out this amazing reel! #aesthetic #vibes"
)

print(result)
# {
#   "status": "success",
#   "facebook_video_id": "123456789",
#   "instagram_media_id": "987654321",
#   "video_url": "https://your-app.onrender.com/reels/20260803_153500/reel.mp4",
#   "facebook_response": {...},
#   "instagram_response": {...}
# }
```

### Individual Platform Upload

```python
from reels import upload_facebook_reel, post_instagram_reel, get_public_video_url

# Upload to Facebook only
fb_video_id = upload_facebook_reel(
    video_path="output/20260803_153500/reel.mp4",
    caption="Facebook only reel"
)

# Upload to Instagram only (requires public URL)
video_url = get_public_video_url("output/20260803_153500/reel.mp4")
ig_response = post_instagram_reel(
    video_url=video_url,
    caption="Instagram only reel"
)
```

---

## 🎬 Upload Pipeline

The complete upload process:

```
1. Validate Video
   ├─ Check file exists
   ├─ Verify it's an MP4
   └─ Log file size

2. Upload to Facebook
   ├─ POST to /videos endpoint
   ├─ Upload MP4 file
   ├─ Publish immediately
   └─ Return video ID

3. Generate Public URL
   ├─ Extract timestamp from path
   └─ Build: {PUBLIC_BASE_URL}/reels/{timestamp}/reel.mp4

4. Wait for Public URL
   ├─ Verify URL returns HTTP 200
   ├─ Retry every 2 seconds
   └─ Timeout after 60 seconds

5. Create Instagram Container
   ├─ POST to /media endpoint
   ├─ media_type: "REELS"
   ├─ video_url: public URL
   └─ Return container ID

6. Poll Container Status
   ├─ GET container status
   ├─ Wait for "FINISHED" status
   ├─ Poll every 3 seconds
   └─ Timeout after 120 seconds

7. Publish to Instagram
   ├─ POST to /media_publish
   ├─ Use container ID
   └─ Return media ID

8. Return Results
   └─ All IDs and responses
```

---

## 🔌 FastAPI Integration

The module automatically integrates with your existing FastAPI server.

### Endpoint: Serve Reel Videos

```
GET /reels/{timestamp}/reel.mp4
```

**Purpose:** Provides a publicly accessible URL for Instagram to download the video.

**Example:**
```bash
curl https://your-app.onrender.com/reels/20260803_153500/reel.mp4
```

**Response:**
- `200 OK`: Returns MP4 video file
- `404 Not Found`: Video doesn't exist

**Usage in Code:**
```python
# This URL is automatically generated and used
video_url = get_public_video_url("output/20260803_153500/reel.mp4")
# Returns: https://your-app.onrender.com/reels/20260803_153500/reel.mp4
```

---

## 🧪 Local Testing

Instagram cannot access `localhost`, so you need to expose your FastAPI server publicly.

### Option 1: Cloudflare Tunnel (Recommended)

```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Start your FastAPI server
python api.py

# In another terminal, create tunnel
cloudflared tunnel --url http://localhost:8000

# Output: https://xxxx.trycloudflare.com
# Update .env:
PUBLIC_BASE_URL=https://xxxx.trycloudflare.com
```

### Option 2: ngrok

```bash
# Install ngrok
brew install ngrok

# Start your FastAPI server
python api.py

# In another terminal, create tunnel
ngrok http 8000

# Output: https://xxxx.ngrok.io
# Update .env:
PUBLIC_BASE_URL=https://xxxx.ngrok.io
```

### Test Upload

```python
from reels import post_reel_to_fb_and_instagram

result = post_reel_to_fb_and_instagram(
    video_path="output/20260803_153500/reel.mp4",
    caption="Test upload"
)

print(result)
```

---

## ⚙️ Configuration

### Timeouts

Adjust in `reels/reel_uploader.py`:

```python
# Facebook video upload timeout
FACEBOOK_TIMEOUT = 300  # 5 minutes

# Instagram container processing timeout
INSTAGRAM_CONTAINER_TIMEOUT = 120  # 2 minutes

# Public URL accessibility timeout
VIDEO_ACCESSIBILITY_TIMEOUT = 60  # 1 minute
```

### Polling Intervals

Adjust in `reels/utils.py`:

```python
# Public URL verification
wait_for_public_video(
    video_url,
    timeout=60,
    retry_interval=2  # Check every 2 seconds
)

# Instagram container status
poll_instagram_container(
    container_id,
    access_token,
    api_version,
    max_wait=120,
    poll_interval=3  # Check every 3 seconds
)
```

---

## 🛡️ Error Handling

### Custom Exceptions

```python
from reels.exceptions import (
    VideoNotFoundError,
    FacebookUploadError,
    InstagramUploadError,
    VideoNotAccessibleError,
    ContainerPollingError,
    PublishError
)

try:
    result = post_reel_to_fb_and_instagram(video_path, caption)
except VideoNotFoundError as e:
    print(f"Video missing: {e}")
except FacebookUploadError as e:
    print(f"Facebook failed: {e}")
    print(f"Status: {e.status_code}")
    print(f"Response: {e.response}")
except InstagramUploadError as e:
    print(f"Instagram failed: {e}")
    print(f"Status: {e.status_code}")
    print(f"Response: {e.response}")
```

### Partial Upload Handling

If Facebook succeeds but Instagram fails:

```python
try:
    result = post_reel_to_fb_and_instagram(video_path, caption)
except InstagramUploadError as e:
    print("✓ Facebook upload succeeded")
    print("✗ Instagram upload failed")
    print(f"Facebook Video ID: {e.facebook_video_id}")  # Still available
    # Reel is on Facebook, can retry Instagram later
```

---

## 📊 Logging

The module provides detailed logging at each step:

```
2026-08-03 11:24:22 - INFO - ============================================================
2026-08-03 11:24:22 - INFO - REEL UPLOAD PIPELINE STARTED
2026-08-03 11:24:22 - INFO - ============================================================
2026-08-03 11:24:22 - INFO - ✓ Video validated: output/20260803_153500/reel.mp4 (15.2 MB)
2026-08-03 11:24:25 - INFO - ✓ Facebook reel uploaded successfully
2026-08-03 11:24:25 - INFO -   Video ID: 123456789
2026-08-03 11:24:25 - INFO - Generated public URL: https://your-app.onrender.com/reels/20260803_153500/reel.mp4
2026-08-03 11:24:27 - INFO - ✓ Video accessible after 2.1s (attempt 2)
2026-08-03 11:24:28 - INFO - ✓ Container created: 987654321
2026-08-03 11:24:35 - INFO - ✓ Container ready after 7.2s (poll 3)
2026-08-03 11:24:36 - INFO - ✓ Instagram reel published successfully
2026-08-03 11:24:36 - INFO -   Media ID: 111222333
2026-08-03 11:24:36 - INFO - ✓ REEL UPLOAD PIPELINE COMPLETED SUCCESSFULLY
```

---

## 📋 Requirements

```python
# Required packages (already in your requirements.txt)
requests>=2.34.0
python-dotenv>=1.2.0
fastapi>=0.140.0
uvicorn>=0.51.0
```

---

## 🔍 Troubleshooting

### "Video not accessible" error

**Problem:** Instagram cannot reach your public URL.

**Solutions:**
1. Verify `PUBLIC_BASE_URL` is set correctly
2. Ensure FastAPI server is running
3. Check firewall/network settings
4. For local testing, ensure tunnel (Cloudflare/ngrok) is active

### "Container polling timeout" error

**Problem:** Instagram is taking longer than 2 minutes to process video.

**Solutions:**
1. Increase `INSTAGRAM_CONTAINER_TIMEOUT` in `reel_uploader.py`
2. Check video file size (recommend < 20MB)
3. Verify video format is valid MP4 (H.264 codec)
4. Check Instagram status: https://developers.facebook.com/status

### "Missing environment variables" error

**Problem:** Required credentials not set.

**Solution:**
```bash
# Check which variables are missing
python -c "from reels import post_reel_to_fb_and_instagram; post_reel_to_fb_and_instagram('test.mp4')"

# Set missing variables in .env
PAGE_ID=...
PAGE_ACCESS_TOKEN=...
IG_USER_ID=...
PUBLIC_BASE_URL=...
```

---

## 🚀 Production Deployment

### Render Configuration

1. **Set Environment Variables** in Render dashboard:
   ```
   PAGE_ID=your_page_id
   PAGE_ACCESS_TOKEN=your_token
   IG_USER_ID=your_ig_id
   API_VERSION=v21.0
   PUBLIC_BASE_URL=https://your-app.onrender.com
   ```

2. **Deploy your app** - The `/reels/{timestamp}/reel.mp4` endpoint is automatically available

3. **Test the endpoint**:
   ```bash
   # Check if video is accessible
   curl -I https://your-app.onrender.com/reels/20260803_153500/reel.mp4
   ```

4. **Upload reels**:
   ```python
   from reels import post_reel_to_fb_and_instagram
   
   result = post_reel_to_fb_and_instagram(
       video_path="output/20260803_153500/reel.mp4",
       caption="Production reel upload!"
   )
   ```

---

## 📖 API Reference

### `post_reel_to_fb_and_instagram(video_path, caption="")`

Complete pipeline - uploads to both platforms.

**Args:**
- `video_path` (str): Path to MP4 video file
- `caption` (str): Caption for both platforms (default: "")

**Returns:**
```python
{
    "status": "success",
    "facebook_video_id": str,
    "instagram_media_id": str,
    "video_url": str,
    "facebook_response": dict,
    "instagram_response": dict
}
```

**Raises:**
- `VideoNotFoundError`: Video doesn't exist
- `FacebookUploadError`: Facebook upload failed
- `InstagramUploadError`: Instagram upload failed
- `VideoNotAccessibleError`: Public URL not accessible

---

### `upload_facebook_reel(video_path, caption="")`

Upload reel to Facebook only.

**Args:**
- `video_path` (str): Path to MP4 video file
- `caption` (str): Video description

**Returns:**
- `str`: Facebook video ID

**Raises:**
- `VideoNotFoundError`: Video doesn't exist
- `FacebookUploadError`: Upload failed

---

### `post_instagram_reel(video_url, caption="")`

Upload reel to Instagram using public URL.

**Args:**
- `video_url` (str): Public URL to MP4 video
- `caption` (str): Reel caption

**Returns:**
- `dict`: Instagram API response with media ID

**Raises:**
- `InstagramUploadError`: Container creation failed
- `VideoNotAccessibleError`: URL not accessible
- `ContainerPollingError`: Container processing failed
- `PublishError`: Publish step failed

---

### `get_public_video_url(video_path)`

Generate public URL for video file.

**Args:**
- `video_path` (str): Local video path (e.g., "output/20260803_153500/reel.mp4")

**Returns:**
- `str`: Public URL (e.g., "https://domain.com/reels/20260803_153500/reel.mp4")

**Raises:**
- `ValueError`: Cannot extract timestamp or PUBLIC_BASE_URL not set

---

## 🔗 Related Documentation

- [Meta Graph API - Video Uploads](https://developers.facebook.com/docs/video-api/guides/publishing)
- [Instagram Graph API - Reels](https://developers.facebook.com/docs/instagram-api/guides/reels)
- [Meta Business SDK](https://developers.facebook.com/docs/business-sdk)

---

## ✅ Testing Checklist

Before deploying to production:

- [ ] All environment variables set
- [ ] FastAPI server running
- [ ] `/reels/{timestamp}/reel.mp4` endpoint accessible
- [ ] Video file exists at correct path
- [ ] Facebook upload succeeds
- [ ] Public URL returns HTTP 200
- [ ] Instagram container created
- [ ] Container status reaches FINISHED
- [ ] Instagram publish succeeds
- [ ] No errors in logs

---

## 🎯 Example: Complete Workflow

```python
from reels import post_reel_to_fb_and_instagram
import json

# 1. Generate reel (your existing code)
# ... (story generation, images, voice, video composition)

# 2. Upload to social media
video_path = "output/20260803_153500/reel.mp4"
caption = "Life is a journey. Embrace every moment. 🌟 #aestheticvibes #wisdom"

try:
    result = post_reel_to_fb_and_instagram(
        video_path=video_path,
        caption=caption
    )
    
    print("✓ Upload successful!")
    print(json.dumps(result, indent=2))
    
except Exception as e:
    print(f"✗ Upload failed: {e}")
```

---

**Module Version:** 1.0.0  
**Last Updated:** 2026-08-03  
**Python Version:** 3.11+  
**Meta Graph API Version:** v21.0

# System Patterns: Aesthetic Vibes

## Architecture Overview

The system uses a **two-pipeline architecture** coordinated by a shared scheduler:

```
GitHub Actions (every 5 min)
        |
        v
smart_scheduler.py (decision engine + locking)
        |
        |-- Quote Pipeline OR Reel Pipeline
        v
Generate -> Upload -> Confirm Success -> Update State
```

## Key Design Patterns

### 1. Scheduler Decision Pattern
`smart_scheduler.py` acts as the central coordinator. It checks:
- IST-based weekly posting windows
- Completed slots (from Gist state)
- Active job lock (prevents quote/reel overlap)
- Minimum spacing (90 min between posts)
- Daily limits (2 quotes, 3 reels per day)

### 2. State Synchronization Pattern
State is stored in GitHub Gist as JSON files:
- `scheduler_state.json` - completed slots, last post times, daily counts, active job lock
- `content_history.json` - last 30 content types for anti-repetition

**Key rule**: State is updated ONLY after confirmed upload success. Failed uploads do not pollute history or mark slots complete.

### 3. Job Locking Pattern
- `acquire_run_lock()` - reserves a slot before generation starts
- `mark_slot_completed()` - clears lock and marks slot done after success
- `release_run_lock()` - clears lock on failure
- Stale locks (older than 60 min) are auto-cleared

### 4. Content Selection Pattern
`content_schedule.py` uses weighted random selection:
- 35 content types organized into morning/evening pools
- Afternoon types split 5/5 between morning and evening pools
- Recent types (last 10 posts) get reduced weight
- History updated only after successful publish

### 5. Event-Aware Content Pattern
`event_detector.py` adds an optional event layer:
- Reads `content_calendar.json` for fixed and dated events
- Enriches prompts with event-specific instructions
- Adds event wishes/hashtags to captions
- Uses event-specific visual cues for image generation
- Supports `EVENT_TEST_DATE` env var for testing

### 6. Quote Pipeline Pattern
```
QuoteGeneration.generate_quote(record_history=False)
  -> PromptSelector.get_prompt_for_current_time()
    -> content_schedule.get_content_type_for_time()
  -> Gemini generates quote text
-> ImageGeneration.create_neon_quote_image()
  -> PIL renders neon-style image from template.jpg
-> FBUpload.schedule_photo_after()
  -> Upload to Facebook, get CDN URL
-> FBUpload.post_to_instagram_from_fb_url()
  -> Create IG container, publish
-> gist_storage.add_to_history() (only after success)
-> smart_scheduler.mark_slot_completed()
```

### 7. Reel Pipeline Pattern
```
api.execute_reel_generation()
  -> Reels_main.generate_complete_reel(upload=False)
    -> Reels.story_generation.generate_story()
      -> Gemini generates story JSON (6 scenes, narration 80-120 words)
    -> Reels.image_generation.generate_images_for_reel()
      -> Cloudflare SDXL generates 6 scene images
    -> Reels.voice_generation.generate_voice()
      -> Edge-TTS generates voiceover (RyanNeural, -15% rate)
    -> Reels.video_generation.create_reel()
      -> MoviePy composes video with subtitles (Whisper base)
  -> Reels.hashtag_generation.generate_hashtags()
  -> Reels.social_upload.upload_reel_to_social_media()
    -> Cloudinary upload for public URL
    -> Facebook video upload
    -> Instagram Reel container create/poll/publish
    -> Delete Cloudinary file after success
  -> Delete local output folder after success
```

### 8. Shared Upload Pattern
`Reels/social_upload.py` centralizes reel upload behavior:
- Returns structured result: `{success, facebook, instagram, cloudinary_url, cloudinary_public_id, errors}`
- Success requires both Facebook and Instagram (current callers)
- Used by both `api.py` and `Reels_main.py`

### 9. Failure Safety Pattern
- **Quote**: Slot marked complete only after all 6 steps succeed (generate → image → FB → IG → history → mark)
- **Reel**: Slot marked complete only after generation + both uploads + cleanup succeed
- **Partial upload caveat**: If Facebook succeeds but Instagram fails, slot not marked complete (may cause duplicate FB post on retry)

### 10. Render Optimization Pattern
`Reels/config.py` detects `RENDER` env var:
- Low-res: 540x960 @ 20fps, 2000k bitrate, no film grain, no zoom
- High-res: 1080x1920 @ 30fps, 8000k bitrate, film grain, Ken Burns zoom

## Module Dependencies

```
smart_scheduler.py -> gist_storage.py (state)
content_schedule.py -> gist_storage.py (history)
PromptSelector.py -> content_schedule.py
QuoteGeneration.py -> PromptSelector.py, event_detector.py
ImageGeneration.py -> QuoteGeneration.py
FBUpload.py -> (Meta Graph API)
api.py -> QuoteGeneration, ImageGeneration, FBUpload, Reels modules
Reels_main.py -> Reels modules, event_detector
Reels/story_generation.py -> Reels/PromptSelector.py, Reels/gender_tracker.py, event_detector
Reels/image_generation.py -> event_detector, Reels/config
Reels/video_generation.py -> Reels/subtitle_generation.py, Reels/config
Reels/social_upload.py -> Reels/cloudinary_uploader.py
Reels/hashtag_generation.py -> event_detector
```

## Concurrency Control
- GitHub Actions `concurrency` group: `aesthetic-vibes-publisher`
- `cancel-in-progress: false` - prevents quote/reel overlap at workflow level
- Scheduler lock in Gist - prevents overlap at application level
# Aesthetic Vibes Technical Architecture

This document explains the current automated publishing architecture for Aesthetic Vibes. It is meant for development and operations reference.

> Note: This file documents the current workflow only. It is not a replacement for the public-facing `Readme.md`.

---

## 1. High-Level System Overview

The repository has two automated content pipelines:

1. **Quote pipeline**
   - Selects a quote content type.
   - Generates text using Gemini.
   - Renders the quote into `image.jpg`.
   - Uploads to Facebook.
   - Uses the Facebook CDN image URL to publish to Instagram.
   - Updates content history and scheduler state only after confirmed upload success.

2. **Reel pipeline**
   - Generates a short story/narration.
   - Generates cinematic images.
   - Generates voiceover.
   - Composes a reel video with subtitles.
   - Uploads the reel to Facebook and Instagram.
   - Deletes temporary output only after confirmed full upload success.

Both pipelines are coordinated by `smart_scheduler.py` and GitHub Actions.

```text ARCHITECTURE.md
GitHub Actions every 5 minutes
        |
        v
smart_scheduler.py
        |
        |-- checks current IST window
        |-- checks completed slots
        |-- checks active job lock
        |-- checks spacing from last post
        |-- checks daily limits
        v
Quote Workflow or Reel Workflow
        |
        v
Generate -> Upload -> Confirm Success
        |
        v
Update Gist state/history only after success
```

---

## 2. Main Runtime Entry Points

| Entry point | Purpose | Used by |
|---|---|---|
| `.github/workflows/quote-scheduler.yml` | Scheduled quote publishing | GitHub Actions |
| `.github/workflows/reel-scheduler.yml` | Scheduled reel generation and publishing | GitHub Actions |
| `api.py` | FastAPI service for health/manual triggers and shared reel execution | Render/manual/GitHub Actions reel workflow |
| `Reels_main.py` | CLI/main reel pipeline | Local/manual/API |
| `smart_scheduler.py` | Shared scheduler decision engine and locking | Both workflows |

---

## 3. Scheduler Architecture

### File: `smart_scheduler.py`

`smart_scheduler.py` is the central coordinator for scheduled publishing.

It handles:

- IST-based weekly posting windows.
- Quote/reel slot detection.
- Minimum spacing between posts.
- Daily quote/reel limits.
- Gist-backed scheduler state.
- Active job locking to prevent quote/reel overlap.
- Slot completion only after confirmed publishing success.

### Scheduler state storage

Scheduler state is stored in GitHub Gist as:

```text ARCHITECTURE.md
scheduler_state.json
```

The Gist ID comes from:

```text ARCHITECTURE.md
SCHEDULER_GIST_ID
```

If `SCHEDULER_GIST_ID` is not configured, scheduler state falls back to the existing content history Gist:

```text ARCHITECTURE.md
CONTENT_HISTORY_GIST_ID
```

This lets one Gist contain both:

```text ARCHITECTURE.md
content_history.json
scheduler_state.json
```

### Scheduler state fields

```json ARCHITECTURE.md
{
  "date": "YYYY-MM-DD",
  "completed_slots": ["morning_quote", "prime_reel"],
  "last_post_time": "ISO UTC timestamp",
  "last_quote_time": "ISO UTC timestamp",
  "last_reel_time": "ISO UTC timestamp",
  "daily_quote_count": 1,
  "daily_reel_count": 2,
  "active_job": {
    "type": "quote",
    "slot": "morning_quote",
    "started_at": "ISO UTC timestamp"
  }
}
```

### Active job lock

Before quote or reel generation starts, the workflow calls:

```text ARCHITECTURE.md
acquire_run_lock(...)
```

After success, `mark_slot_completed(...)` clears the lock.

After failure, the workflow calls:

```text ARCHITECTURE.md
release_run_lock(...)
```

A lock older than 60 minutes is treated as stale and can be cleared automatically.

### Daily reset

The scheduler resets daily counters using IST date, not UTC date, because the posting windows are defined in IST.

---

## 4. Current Posting Schedule

The workflows run every 5 minutes, but actual publishing only happens inside valid windows.

### Ideal Daily 4-Post Schedule

The daily schedule follows this timeline (all times IST):

| Time IST | Post | Type |
|---:|---|---|
| 8:00 AM | Quote 1 | Morning energy content |
| 12:00 PM | Reel 1 | Lunch-break video entertainment |
| 4:00 PM | Quote 2 | Late-afternoon / end-of-work commute |
| 8:00 PM | Reel 2 | Peak evening unwind window |

### Quote schedule

Quotes have two slots per day:

| Slot | Typical time IST | Purpose |
|---|---:|---|
| `morning_quote` | Morning | Morning/light content |
| `evening_quote` | Evening | Evening/deep content |

Daily quote limit:

```text ARCHITECTURE.md
2 quotes/day
```

### Reel schedule

Reels have two slots per day:

| Slot | Typical time IST | Purpose |
|---|---:|---|
| `afternoon_reel` | ~12:00 PM | Lunch-break quick video entertainment |
| `prime_reel` | ~8:00 PM | Peak evening unwind window |

Daily reel limit: 2 reels/day

Reels can start generation 25 minutes before the actual posting window so the final upload lands closer to the intended time.

---

## 5. Quote Content Selection Architecture

### Files involved

| File | Role |
|---|---|
| `content_schedule.py` | Selects the content type based on time and recent history |
| `PromptSelector.py` | Maps selected content type to exact Gemini prompt |
| `QuoteGeneration.py` | Sends prompt to Gemini and returns generated text |
| `gist_storage.py` | Stores content type history in Gist |

### Content type pools

The quote scheduler only posts in morning and evening. To avoid losing afternoon content types, the afternoon group is split 5/5 into active morning/evening quote pools.

Original groups still exist:

| Original group | Count |
|---|---:|
| `MORNING_ENERGY_TYPES` | 8 |
| `AFTERNOON_RELATABLE_TYPES` | 10 |
| `EVENING_DEEP_TYPES` | 17 |
| Total unique content types | 35 |

Active quote pools:

| Active pool | Contents | Count |
|---|---|---:|
| `MORNING_QUOTE_TYPES` | Original morning + 5 afternoon types | 13 |
| `EVENING_QUOTE_TYPES` | Original evening + 5 afternoon types | 22 |

### Afternoon split

Morning receives these afternoon types:

```text ARCHITECTURE.md
FUNNY_SASSY
POP_CULTURE_LYRICS
DAILY_STRUGGLE_HUMOR
FOOD_COMFORT
WHOLESOME_JOY
```

Evening receives these afternoon types:

```text ARCHITECTURE.md
BITTERSWEET_RELATABLE
SHORT_CONVERSATION
HE_SHE_RELATIONSHIP
SOCIAL_COMMENTARY
FRIENDSHIP_BONDS
```

### Quote content selection flow

```text ARCHITECTURE.md
Quote workflow
  -> QuoteGeneration.generate_quote(record_history=False)
    -> PromptSelector.get_prompt_for_current_time(record_history=False)
      -> content_schedule.get_content_type_for_time(record_history=False)
        -> get_time_category()
          -> 5 AM - 5 PM IST: MORNING_QUOTE_TYPES
          -> 5 PM - 5 AM IST: EVENING_QUOTE_TYPES
        -> get_content_history()
        -> weighted random selection avoiding recent repeats
      -> PromptSelector stores LAST_SELECTED_CONTENT_INFO
    -> Gemini generates quote text
```

### History update rule

For scheduled quote workflow, content history is **not** updated during generation.

Instead:

1. Quote is generated.
2. Image is created.
3. Facebook upload succeeds.
4. Instagram publish succeeds.
5. Only then `gist_storage.add_to_history(...)` is called.

This prevents failed quote uploads from polluting content history.

---

## 6. Quote Publishing Workflow

### File: `.github/workflows/quote-scheduler.yml`

The quote workflow runs every 5 minutes:

```yaml ARCHITECTURE.md
schedule:
  - cron: '0,15,30,45 * * * *'
```

It uses GitHub Actions concurrency:

```yaml ARCHITECTURE.md
concurrency:
  group: aesthetic-vibes-publisher
  cancel-in-progress: false
```

This prevents quote and reel workflows from running at the same time at the GitHub Actions level.

### Quote workflow steps

```text ARCHITECTURE.md
1. Checkout repository
2. Set up Python 3.11
3. Install requirements.txt
4. Run smart_scheduler.should_publish_quote()
5. If false: skip
6. If true:
   a. get active quote window
   b. acquire scheduler lock
   c. generate quote without recording history
   d. create image.jpg
   e. upload image to Facebook
   f. publish image to Instagram from Facebook CDN URL
   g. add selected content type to content history
   h. mark scheduler slot completed
   i. delete temporary image.jpg
7. On failure:
   a. release scheduler lock
   b. fail the workflow
```

### Quote publishing file responsibilities

| File | Responsibility |
|---|---|
| `QuoteGeneration.py` | Generates the text quote from Gemini |
| `PromptSelector.py` | Chooses the exact prompt template |
| `content_schedule.py` | Chooses the content type and avoids recent repeats |
| `ImageGeneration.py` | Creates `image.jpg` using `template.jpg` |
| `FBUpload.py` | Uploads image to Facebook and Instagram |
| `gist_storage.py` | Updates content history after success |
| `smart_scheduler.py` | Locks job and marks slot complete after success |

---

## 7. Reel Generation Architecture

### Main reel files

| File | Role |
|---|---|
| `Reels_main.py` | Orchestrates the full reel generation pipeline |
| `Reels/story_generation.py` | Generates reel story/narration |
| `Reels/image_generation.py` | Generates scene images |
| `Reels/voice_generation.py` | Generates voiceover audio |
| `Reels/video_generation.py` | Composes final `reel.mp4` |
| `Reels/subtitle_generation.py` | Generates subtitles using Whisper base model |
| `Reels/hashtag_generation.py` | Generates reel hashtags |
| `Reels/social_upload.py` | Shared Facebook/Instagram/Cloudinary reel uploader |
| `api.py` | Executes reel generation for workflow/API and raises on upload failure |

### Reel generation flow

```text ARCHITECTURE.md
Reel workflow
  -> api.execute_reel_generation()
    -> Reels_main.generate_complete_reel(upload=False)
      -> Reels.story_generation.generate_story()
      -> Reels.image_generation.generate_images_for_reel()
      -> Reels.voice_generation.generate_voice()
      -> Reels.video_generation.create_reel()
      -> returns output folder + reel.mp4 + story data
    -> Reels.hashtag_generation.generate_hashtags()
    -> Reels.social_upload.upload_reel_to_social_media()
      -> upload video to Cloudinary for Instagram public URL
      -> upload video to Facebook page videos endpoint
      -> create Instagram Reel media container
      -> poll Instagram container status
      -> publish Instagram Reel
      -> delete Cloudinary file after Instagram success
    -> if upload success is false: raise RuntimeError
    -> if upload success is true: delete local output folder
```

---

## 8. Reel Publishing Workflow

### File: `.github/workflows/reel-scheduler.yml`

The reel workflow also runs every 5 minutes:

```yaml ARCHITECTURE.md
schedule:
  - cron: '0,15,30,45 * * * *'
```

It shares the same concurrency group as quote workflow:

```yaml ARCHITECTURE.md
concurrency:
  group: aesthetic-vibes-publisher
  cancel-in-progress: false
```

### Reel workflow steps

```text ARCHITECTURE.md
1. Checkout repository
2. Set up Python 3.11
3. Install ffmpeg
4. Install requirements.txt
5. Restore/cache Whisper base model
6. Run smart_scheduler.should_publish_reel()
7. If false: skip
8. If true:
   a. get active reel window
   b. acquire scheduler lock
   c. call api.execute_reel_generation()
   d. generate story/images/voice/video
   e. upload to Facebook and Instagram using shared uploader
   f. if upload success true, delete output folder
   g. mark scheduler slot completed
9. On failure:
   a. release scheduler lock
   b. keep output folder for debugging if available
   c. fail workflow
```

---

## 9. Shared Reel Upload Architecture

### File: `Reels/social_upload.py`

This file centralizes reel upload behavior so `api.py` and `Reels_main.py` do not maintain separate upload implementations.

Main function:

```text ARCHITECTURE.md
upload_reel_to_social_media(...)
```

Structured result shape:

```json ARCHITECTURE.md
{
  "success": false,
  "facebook": null,
  "instagram": null,
  "cloudinary_url": null,
  "cloudinary_public_id": null,
  "errors": []
}
```

Success is true only when required platforms are successful:

```text ARCHITECTURE.md
facebook_ok = bool(results["facebook"]) or not require_facebook
instagram_ok = bool(results["instagram"]) or not require_instagram
success = facebook_ok and instagram_ok
```

Current callers require both Facebook and Instagram success.

---

## 10. Gist Storage Architecture

### Content history

File:

```text ARCHITECTURE.md
gist_storage.py
```

Gist file:

```text ARCHITECTURE.md
content_history.json
```

Used for quote content type anti-repetition.

History stores selected content type strings:

```json ARCHITECTURE.md
[
  "MOTIVATIONAL_INSPIRING",
  "DEEP_EMOTIONAL",
  "FUNNY_SASSY"
]
```

Only the last 30 entries are kept.

### Scheduler state

File:

```text ARCHITECTURE.md
smart_scheduler.py
```

Gist file:

```text ARCHITECTURE.md
scheduler_state.json
```

Used for:

- completed slots
- last post time
- daily counts
- active job lock

---

## 11. Failure and Safety Behavior

### Quote safety

A quote slot is marked completed only after:

1. Gemini quote generation succeeds.
2. `image.jpg` is created.
3. Facebook returns a CDN URL.
4. Instagram returns a post ID.
5. Content history is updated.
6. `mark_slot_completed(...)` succeeds.

If anything fails before slot completion:

- scheduler lock is released,
- workflow fails,
- slot remains uncompleted for possible retry.

### Reel safety

A reel slot is marked completed only after:

1. reel generation succeeds,
2. Facebook upload returns a video ID,
3. Instagram publish returns a post ID,
4. shared uploader returns `success=True`,
5. local output folder is deleted,
6. `mark_slot_completed(...)` succeeds.

If anything fails:

- scheduler lock is released,
- output folder is kept for debugging where possible,
- workflow fails,
- slot remains uncompleted for possible retry.

### Known partial-upload caveat

If Facebook upload succeeds but Instagram fails, the slot is not marked complete. This is intentional because current success criteria require both platforms.

However, a future retry may create a duplicate Facebook post unless partial-upload reconciliation is added later.

Possible future improvement:

```text ARCHITECTURE.md
Store partial Facebook post/video ID in scheduler_state.json and delete or reuse it if Instagram fails.
```

---

## 12. Environment Variables

### Shared scheduler/history variables

| Variable | Purpose |
|---|---|
| `SCHEDULER_GIST_ID` | Optional dedicated scheduler-state Gist |
| `CONTENT_HISTORY_GIST_ID` | Content history Gist; scheduler fallback if no scheduler Gist is set |
| `GH_TOKEN` or `GITHUB_TOKEN` | GitHub token with Gist access |

### Quote variables

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini quote generation |
| `PAGE_ID` | Facebook Page ID |
| `PAGE_ACCESS_TOKEN` | Facebook/Instagram Graph API token |
| `API_VERSION` | Graph API version |
| `IG_USER_ID` | Instagram Business user ID |

### Reel variables

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Story generation |
| `HF_TOKEN`, `HF_TOKEN2` | Image generation providers if used |
| `ELEVENLABS_API_KEY` | Voice generation |
| `CF_ACCOUNT_ID_1`, `CF_TOKEN_1` | Primary Cloudflare image generation account/token |
| `CF_ACCOUNT_ID_2`, `CF_TOKEN_2` | Secondary Cloudflare account/token |
| `CF_ACCOUNT_ID_3`–`CF_ACCOUNT_ID_8`, `CF_TOKEN_3`–`CF_TOKEN_8` | Fallback Cloudflare accounts used for rate-limit load balancing |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary hosting |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `AUTO_UPLOAD_REELS` | Controls CLI auto-upload behavior |

---

## 13. Operational Flow Summary

### Normal quote run

```text ARCHITECTURE.md
GitHub Actions quote-scheduler
  -> smart_scheduler says publish
  -> lock acquired in scheduler_state.json
  -> content type selected from morning/evening merged pool
  -> prompt selected
  -> Gemini quote generated
  -> image.jpg rendered
  -> Facebook image uploaded
  -> Instagram image published
  -> content_history.json updated
  -> scheduler_state.json marks slot complete
  -> image.jpg removed
```

### Normal reel run

```text ARCHITECTURE.md
GitHub Actions reel-scheduler
  -> smart_scheduler says generate
  -> lock acquired in scheduler_state.json
  -> story generated
  -> images generated
  -> voice generated
  -> subtitles/video composed
  -> video uploaded to Cloudinary
  -> video uploaded to Facebook
  -> Instagram Reel container created/polled/published
  -> Cloudinary video deleted after Instagram success
  -> output folder deleted
  -> scheduler_state.json marks slot complete
```

---

## 14. How to Read Workflow Logs

### Quote workflow success indicators

Look for:

```text ARCHITECTURE.md
ALL CHECKS PASSED - PUBLISH QUOTE
Active job lock acquired
Quote generated
Image created
Facebook upload complete
Instagram post complete
Marking slot "..." as completed
QUOTE POSTED SUCCESSFULLY
```

### Reel workflow success indicators

Look for:

```text ARCHITECTURE.md
ALL CHECKS PASSED - START REEL GENERATION
Active job lock acquired
REEL GENERATION STARTED
Reel generation completed successfully
Social upload completed successfully
REEL GENERATION AND UPLOAD COMPLETE
Marking slot "..." as completed
```

### Skip indicators

A workflow can safely skip when:

```text ARCHITECTURE.md
Not in a posting window
Slot already completed today
Need more minutes before next post
Daily quote/reel limit reached
Another job is running
```

---

## 15. Current Design Guarantees

The current architecture guarantees:

- quote and reel workflows do not intentionally overlap,
- duplicate slot completion is avoided,
- daily reset follows IST,
- content history updates only after successful quote publish,
- scheduler slot completion happens only after confirmed upload success,
- reel upload behavior is shared and consistent,
- all 35 quote content types are reachable through morning/evening scheduled quote runs,
- no content is published outside the safe IST window (06:00–21:00), and the `late_reel`
  odd-hour slot has been removed,
- exactly 4 posts per day: 8:00 AM quote, 12:00 PM reel, 4:00 PM quote, 8:00 PM reel.

---

## 16. Recommended Manual Validation

After changing workflow or scheduler logic, manually run:

```bash ARCHITECTURE.md
python3 -m py_compile smart_scheduler.py gist_storage.py content_schedule.py PromptSelector.py QuoteGeneration.py Reels/social_upload.py Reels_main.py api.py Reels/subtitle_generation.py
```

Then test GitHub Actions with `workflow_dispatch`:

1. Run Quote Scheduler manually.
2. Confirm lock acquisition/release.
3. Confirm `scheduler_state.json` exists in the Gist.
4. Confirm `content_history.json` updates only after quote publish success.
5. Run Reel Scheduler manually.
6. Confirm output cleanup only after full upload success.

---

## 17. Files by Responsibility

| Area | Files |
|---|---|
| GitHub Actions scheduling | `.github/workflows/quote-scheduler.yml`, `.github/workflows/reel-scheduler.yml` |
| Scheduler and locking | `smart_scheduler.py` |
| Quote content selection | `content_schedule.py`, `PromptSelector.py`, `QuoteGeneration.py` |
| Quote image rendering | `ImageGeneration.py`, `template.jpg`, `Fonts/` |
| Quote publishing | `FBUpload.py` |
| History storage | `gist_storage.py` |
| Reel orchestration | `Reels_main.py`, `api.py` |
| Reel generation modules | `Reels/story_generation.py`, `Reels/image_generation.py`, `Reels/voice_generation.py`, `Reels/video_generation.py`, `Reels/subtitle_generation.py` |
| Reel upload | `Reels/social_upload.py`, `Reels/cloudinary_uploader.py` |
| Public README | `Readme.md` |

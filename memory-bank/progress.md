# Progress: Aesthetic Vibes

## Project Status: ACTIVE

## What Works
- ✅ **Quote pipeline** - Fully automated via GitHub Actions
  - Gemini quote generation (35 content types)
  - Neon image rendering with PIL
  - Facebook + Instagram publishing
  - Content history tracking in Gist
- ✅ **Reel pipeline** - Fully automated via GitHub Actions
  - Gemini story generation (6 scenes, 80-120 word narration)
  - Cloudflare SDXL image generation (with account fallback)
  - Edge-TTS voiceover generation
  - MoviePy video composition with Whisper subtitles
  - Cloudinary video hosting for Instagram
  - Facebook + Instagram reel publishing
- ✅ **Smart scheduler** - IST-based weekly windows
  - 2 quote slots + 3 reel slots per day
  - Active job locking (60 min stale timeout)
  - Minimum 90 min spacing between posts
  - Daily limits (2 quotes, 3 reels)
  - Gist-backed state synchronization
- ✅ **Event detection** - Date-aware content enhancement
  - Fixed events (annual) and dated events (specific dates)
  - Event-specific prompts, captions, hashtags, and visual cues
  - `EVENT_TEST_DATE` env var for testing
  - Date-name lookup files for 2026 events
- ✅ **API service** - FastAPI on Render
  - Health check endpoint
  - Manual autopilot trigger
  - Reel generation endpoint
  - Video serving for legacy uploader

## What's In Progress
- 🔄 **Event detection enhancements** - Recent updates to support date-name lookup files
- 🔄 **Content calendar** - Continuously growing with Indian festivals and cultural events

## What's Blocked / Not Started
- ⏳ **Partial-upload reconciliation** - Known caveat: if Facebook succeeds but Instagram fails, retry may create duplicate Facebook post
- ⏳ **Automated testing** - No formal test suite exists; validation is manual via `py_compile` and workflow_dispatch
- ⏳ **Vosk subtitle alternative** - Implemented but not active (Whisper is primary; Vosk commented out in requirements)

## Known Issues
1. **Partial upload caveat** - Facebook success + Instagram failure leaves slot uncompleted; retry may duplicate Facebook post
2. **Cloudflare quota** - Multiple accounts configured but all could be exhausted simultaneously
3. **Render memory** - 512MB RAM limit requires low-res video settings (540x960 @ 20fps)
4. **Gemini model dependency** - Uses `gemini-3.6-flash` which may change availability

## Recent Milestones
- **Event detection enhancement** - Added support for separate date-name lookup JSON files
- **2026 event calendar** - Comprehensive list of Indian festivals and cultural events
- **Shared reel uploader** - Centralized upload logic in `Reels/social_upload.py`
- **Scheduler state in Gist** - Moved from local files to Gist-backed state

## Next Milestones
1. Add partial-upload reconciliation for Facebook/Instagram failures
2. Add automated testing for scheduler logic
3. Review and expand content calendar
4. Consider adding more content types or refining prompts
5. Monitor event detection with new date-name lookup files

## Validation Commands
```bash
# Syntax check all core modules
python3 -m py_compile smart_scheduler.py gist_storage.py content_schedule.py PromptSelector.py QuoteGeneration.py Reels/social_upload.py Reels_main.py api.py Reels/subtitle_generation.py

# Test scheduler decision
python3 smart_scheduler.py

# Test content selection
python3 content_schedule.py

# Test event detection (with test date)
EVENT_TEST_DATE=2026-08-15 python3 -c "from event_detector import get_today_event; print(get_today_event())"
# Active Context: Aesthetic Vibes

## Current Work Focus
The project is actively maintained with recent updates to the event detection system. The `event_detector.py` was recently modified to support loading date-to-event-name mappings from separate JSON lookup files (`event_date_lookup_2026.json`, `event_date_lookup.json`).

## Recent Changes
- **event_detector.py** - Enhanced to support:
  - Loading date-name lookups from separate JSON files (`event_date_lookup_2026.json`, `event_date_lookup.json`)
  - Normalizing calendar data from various formats (event_details, event_meta, event_lookup, etc.)
  - Merging event details from lookup files with calendar data
  - Supporting both flat calendar data and structured event metadata

## Current State
- **Quote pipeline**: Fully operational via GitHub Actions (every 5 min)
- **Reel pipeline**: Fully operational via GitHub Actions (every 5 min)
- **Event system**: Enhanced with date-name lookup support for 2026 events
- **Scheduler**: Uses Gist-backed state with active job locking
- **Content calendar**: Contains 20+ fixed events and 20+ dated events for 2026

## Active Development Areas
1. **Event detection enhancements** - Recent work on date-name lookup files
2. **Content calendar** - Growing list of Indian festivals and cultural events
3. **Reel generation** - Cloudflare image generation with fallback accounts
4. **Scheduler reliability** - Gist state synchronization and lock management

## Key Decisions & Their Rationale
1. **Gist-based state storage** - Avoids local file persistence issues in ephemeral GitHub Actions runners
2. **History update after success only** - Prevents failed uploads from polluting content history
3. **Shared reel uploader** - Centralizes upload logic in `Reels/social_upload.py` for consistency
4. **IST-based scheduling** - Posting windows defined in IST for optimal South Asian engagement
5. **Event-aware content** - Adds cultural relevance without disrupting normal random content flow
6. **Cloudflare for image generation** - Free tier with multiple account fallback for quota management
7. **Edge-TTS for voiceover** - Free alternative to ElevenLabs (which is commented out in requirements)

## Current Risks & Considerations
1. **Partial upload caveat** - If Facebook succeeds but Instagram fails, slot not marked complete; retry may create duplicate Facebook post
2. **Cloudflare quota limits** - Multiple accounts configured as fallback, but all could be exhausted
3. **Whisper model download** - ~74MB model needs to be cached in GitHub Actions (handled via cache step)
4. **Render memory constraints** - 512MB RAM limit requires low-res video settings
5. **Gemini model dependency** - Uses `gemini-3.6-flash` which may change availability

## Next Steps / Pending Work
- Monitor event detection with new date-name lookup files
- Consider adding partial-upload reconciliation for Facebook/Instagram failures
- Potentially add more content types or refine existing prompts
- Consider adding automated testing for scheduler logic
- Review and update content calendar for upcoming events

## Environment Notes
- Current date: 15/08/2026 (Independence Day in India - event mode active)
- `event_date_lookup_2026.json` contains 2026 dated events
- `content_calendar.json` contains both fixed and dated events
- Both quote and reel workflows run every 5 minutes via GitHub Actions
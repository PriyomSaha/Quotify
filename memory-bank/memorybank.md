# Aesthetic Vibes Memory Bank

This memory bank provides a comprehensive knowledge base for the Aesthetic Vibes content automation project. It is designed to be loaded at the start of each session to provide full context about the project.

## Core Files

| File | Purpose |
|---|---|
| [projectbrief.md](projectbrief.md) | Project overview, mission, capabilities, and entry points |
| [productContext.md](productContext.md) | Why the project exists, problems it solves, user journeys |
| [systemPatterns.md](systemPatterns.md) | Architecture, design patterns, module dependencies |
| [techContext.md](techContext.md) | Technology stack, environment variables, file structure |
| [activeContext.md](activeContext.md) | Current work focus, recent changes, active decisions |
| [progress.md](progress.md) | What works, what's in progress, known issues, milestones |

## Quick Reference

### Project Identity
- **Name**: Aesthetic Vibes
- **Social**: Instagram `@aesthetic_o_vibes`, Facebook `AesthaticsVibes`
- **Purpose**: Automated emotional quote and cinematic reel generation for South Asian audience
- **Stack**: Python 3.11, FastAPI, GitHub Actions, Render, Gemini, Cloudflare, Edge-TTS, Whisper, MoviePy, Cloudinary

### Two Pipelines
1. **Quote Pipeline**: Gemini → PIL neon image → Facebook → Instagram
2. **Reel Pipeline**: Gemini story → Cloudflare images → Edge-TTS voice → MoviePy video → Cloudinary → Facebook/Instagram

### Scheduler
- Runs every 5 min via GitHub Actions
- IST-based weekly windows (2 quotes + 3 reels/day)
- Gist-backed state with active job locking
- 90 min minimum spacing, 60 min stale lock timeout

### Key Environment Variables
- `GEMINI_API_KEY`, `PAGE_ID`, `PAGE_ACCESS_TOKEN`, `API_VERSION`, `IG_USER_ID`
- `SCHEDULER_GIST_ID`, `CONTENT_HISTORY_GIST_ID`, `GH_TOKEN`
- `CF_ACCOUNT_ID_1/2`, `CF_TOKEN_1/2`
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- `EVENT_TEST_DATE` (testing), `FORCE_PUBLISH` (testing)

### Content System
- 35 content types across morning/afternoon/evening pools
- Weighted random selection avoiding recent repeats
- Event-aware enhancement via `content_calendar.json` and `event_date_lookup_2026.json`

### Known Caveats
- Partial upload: FB success + IG failure leaves slot uncompleted (may duplicate FB post on retry)
- Cloudflare quota limits with multi-account fallback
- Render 512MB RAM requires low-res video settings

## Usage
Load the relevant memory bank files at the start of each session to understand the project context before making changes. The `activeContext.md` file should be updated whenever significant work is completed.
# Technical Context: Aesthetic Vibes

## Technology Stack

### Core Languages & Frameworks
- **Python 3.11** - Primary language
- **FastAPI** - API service (api.py)
- **Uvicorn** - ASGI server

### AI/ML Services
| Service | Purpose | Model |
|---|---|---|
| **Google Gemini** | Quote generation, story generation | `gemini-3.6-flash` |
| **Cloudflare Workers AI** | Scene image generation | `@cf/stabilityai/stable-diffusion-xl-base-1.0` |
| **Edge-TTS** | Voiceover generation | `en-GB-RyanNeural` (rate -15%, pitch -5Hz) |
| **OpenAI Whisper** | Subtitle generation | `base` model (74MB) |
| **Vosk** (optional) | Alternative subtitle generation | `vosk-model-small-en-us-0.15` (40MB) |

### Cloud Services
| Service | Purpose |
|---|---|
| **GitHub Actions** | Scheduled workflows (every 5 min) |
| **GitHub Gist** | State storage (scheduler_state.json, content_history.json) |
| **Render** | FastAPI hosting, health checks |
| **Cloudinary** | Video hosting for Instagram public URLs |
| **Meta Graph API** | Facebook/Instagram publishing |

### Key Python Libraries
- `google-genai` - Gemini API
- `Pillow` - Image processing
- `moviepy` - Video composition
- `openai-whisper` - Speech-to-text for subtitles
- `edge-tts` - Text-to-speech
- `cloudinary` - Cloud video hosting
- `requests` - HTTP client
- `fastapi` / `uvicorn` - API framework
- `python-dotenv` - Environment variables
- `numpy` - Numerical operations
- `torch` - Whisper dependency

## Environment Variables

### Scheduler/History
| Variable | Purpose |
|---|---|
| `SCHEDULER_GIST_ID` | Dedicated scheduler-state Gist (optional) |
| `CONTENT_HISTORY_GIST_ID` | Content history Gist; scheduler fallback |
| `GH_TOKEN` / `GITHUB_TOKEN` | GitHub token with Gist access |

### Quote Pipeline
| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini quote generation |
| `PAGE_ID` | Facebook Page ID |
| `PAGE_ACCESS_TOKEN` | Facebook/Instagram Graph API token |
| `API_VERSION` | Graph API version (default: v21.0) |
| `IG_USER_ID` | Instagram Business user ID |

### Reel Pipeline
| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Story generation |
| `HF_TOKEN`, `HF_TOKEN2` | Hugging Face tokens (backup image providers) |
| `ELEVENLABS_API_KEY` | ElevenLabs voice (currently unused, Edge-TTS used) |
| `CF_ACCOUNT_ID_1`, `CF_TOKEN_1` | Primary Cloudflare account |
| `CF_ACCOUNT_ID_2`, `CF_TOKEN_2` | Secondary Cloudflare account |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `AUTO_UPLOAD_REELS` | Controls CLI auto-upload (default: true) |
| `PUBLIC_BASE_URL` | Base URL for serving reel videos (legacy reel_uploader) |

### Testing
| Variable | Purpose |
|---|---|
| `EVENT_TEST_DATE` | Simulate a specific date for event testing (e.g., `2026-08-15`) |
| `FORCE_PUBLISH` | Bypass scheduler window for manual testing |
| `NO_UPLOAD_QUOTES` | Skip upload in Photos_main.py |

## Posting Schedule (IST)

### Quote Slots (2/day)
| Slot | Time (IST) | Priority |
|---|---|---|
| `morning_quote` | 8:00-9:00 (varies by day) | 3 |
| `evening_quote` | 18:15-19:45 (varies by day) | 3 |

### Reel Slots (3/day)
| Slot | Time (IST) | Priority |
|---|---|---|
| `afternoon_reel` | 12:45-16:15 (varies by day) | 4 |
| `prime_reel` | 20:00-21:45 (varies by day) | 5 |
| `late_reel` | 22:00-23:45 (varies by day) | 4 |

### Timing Constants
- `MIN_SPACING_MINUTES = 90` - Minimum between any two posts
- `REEL_GENERATION_TIME = 25` - Minutes needed to generate a reel
- `WINDOW_GRACE_PERIOD = 30` - Minutes after window closes to still publish
- `QUOTE_LOOKAHEAD_MINUTES = 5` - Buffer before quote window starts
- `MISSED_WINDOW_RECOVERY_MINUTES = 90` - Late quote recovery window
- `ACTIVE_JOB_TIMEOUT_MINUTES = 60` - Clear stale generation locks

## Content Type System

### 35 Content Types
Organized into 3 original groups:
- **Morning Energy (8)**: Motivational, Elder Wisdom, Gratitude, Success, Dreams, Life Lessons, Small Victories, Music & Art
- **Afternoon Relatable (10)**: Funny/Sassy, Bittersweet, Short Conversation, He/She Relationship, Pop Culture, Daily Struggle, Food, Social Commentary, Friendship, Wholesome
- **Evening Deep (17)**: Deep Emotional, Nature/Universe, Life Wisdom, One-Liner, Hidden Truths, Unpopular Opinion, Childhood vs Now, Self-Love, Mental Health, Philosophical, Overthinking, Growth, Late Night, Forgiveness, Time, Truth Bombs, Travel

### Active Quote Pools
- **Morning Pool (13)**: 8 morning + 5 afternoon types
- **Evening Pool (22)**: 17 evening + 5 afternoon types

## File Structure

```
QuotesGenerator/
├── .github/workflows/
│   ├── quote-scheduler.yml    # Quote publishing workflow
│   └── reel-scheduler.yml     # Reel generation workflow
├── Reels/
│   ├── __init__.py            # Module exports
│   ├── config.py              # Central configuration
│   ├── cloudinary_uploader.py # Cloudinary video hosting
│   ├── exceptions.py          # Custom exceptions
│   ├── gender_tracker.py      # Visual mode selection
│   ├── hashtag_generation.py  # Reel caption/hashtags
│   ├── image_generation.py    # Cloudflare scene images
│   ├── PromptSelector.py      # Reel prompt selection
│   ├── reel_uploader.py       # Legacy reel uploader
│   ├── social_upload.py       # Shared reel uploader
│   ├── story_generation.py    # Gemini story generation
│   ├── subtitle_generation.py # Whisper subtitles
│   ├── subtitle_generation_vosk.py # Vosk alternative
│   ├── utils.py               # Upload utilities
│   ├── video_generation.py    # MoviePy video composition
│   ├── voice_generation.py    # Edge-TTS voiceover
│   └── inputs/                # Background music assets
├── Fonts/
│   ├── Kaushan_Script/        # Logo font
│   └── Montserrat/            # Subtitle font
├── api.py                     # FastAPI service
├── ARCHITECTURE.md            # Technical architecture doc
├── check_last_post.py         # Facebook last-post checker
├── content_calendar.json      # Event calendar
├── content_schedule.py        # Content type selection
├── create_gist_simple.py      # Gist creation helper
├── cron_autopilot.py          # Direct cron script
├── event_detector.py          # Event detection
├── FBUpload.py                # Quote photo upload
├── gist_storage.py            # Gist state storage
├── ImageGeneration.py         # Neon quote image
├── PageAccessTokenGenerate.py # Token generation helper
├── Photos_main.py             # Manual quote pipeline
├── ProfilePic.jpg             # Profile picture
├── PromptSelector.py          # Quote prompt selection
├── QuoteGeneration.py         # Gemini quote generation
├── Reels_main.py              # Reel pipeline orchestrator
├── requirements.txt           # Dependencies
├── smart_scheduler.py         # Scheduler engine
├── template.jpg               # Quote image template
└── Readme.md                  # Public README
```

## Deployment Configuration

### GitHub Actions
- **Quote workflow**: Python 3.11, timeout 10 min, runs every 5 min
- **Reel workflow**: Python 3.11 + ffmpeg, timeout 40 min, runs every 5 min, caches Whisper model
- Both use `concurrency: aesthetic-vibes-publisher` with `cancel-in-progress: false`

### Render
- FastAPI app on port 8000 (or `PORT` env)
- Health check at `/health`
- Manual triggers at `/autopilot` and `/generate-reel`
- Serves reel videos at `/reels/{timestamp}/reel.mp4`
- 10-minute keep-alive timeout for video processing
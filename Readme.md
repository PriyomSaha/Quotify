# Aesthetic Vibes - Automated Quote Publishing System

## 📋 Project Overview

**"We are not a poet, Just a lost soul finding combination of words to bring you home"**

An automated content generation and publishing system for the Instagram/Facebook page "Aesthetic Vibes" (55K followers). The system creates AI-generated diverse content with **33 unique content types**, renders them as neon-styled images, and automatically publishes to social media platforms.

**Pipeline Flow:** Content Type Selection → AI Content Generation → Neon Image Creation → Facebook Upload → Instagram Publishing

**Posting Schedule:** 17 posts per day with 2-hour minimum spacing between posts

**Smart Features:**
- 33 diverse content types organized by time-appropriate energy
- Anti-repetition tracking via GitHub Gist (last 30 posts)
- Weighted random selection (unused types get 3x priority)
- Time-based categories (morning energetic, afternoon relatable, evening deep)
- Automatic spacing enforcement (prevents duplicate posts even with multiple triggers)

---

## 🎯 Content System - 33 Diverse Types

### Smart Randomization Engine

- **33 unique content types** organized by time-appropriate energy
- **Smart anti-repetition** - tracks last 30 posts via GitHub Gist
- **Weighted selection** - unused types get 3x priority
- **Time-based categories** - morning energetic, afternoon relatable, evening deep
- **2-hour minimum spacing** - prevents duplicate posts even with multiple triggers

### Morning Energy (5 AM - 12 PM IST) - 8 Types

1. **Motivational/Inspiring** - Action-oriented encouragement
2. **Elder Wisdom** - "Father/Mother used to say..." cultural wisdom
3. **Gratitude/Mindful** - Simple joys and appreciation
4. **Success/Hustle** - Ambitious goal-oriented messages
5. **Dreams & Ambitions** - Side hustle and passion project energy
6. **Life Lessons** - Practical wisdom from experience
7. **Small Victories** - Celebrating tiny wins
8. **Music & Art** - Creative healing and inspiration

### Afternoon Relatable (12 PM - 5 PM IST) - 10 Types

1. **Funny/Sassy** - Witty self-aware humor
2. **Bittersweet Relatable** - Gen-Z modern behavior moments
3. **Short Conversation** - Authentic dialogue snippets
4. **He/She Relationship** - Modern dating observations
5. **Pop Culture/Lyrics** - Trending references
6. **Daily Struggle Humor** - Work, family, money stress
7. **Food & Comfort** - Emotional food connections
8. **Social Commentary** - Gentle modern culture critique
9. **Friendship & Bonds** - Platonic love appreciation
10. **Wholesome/Joy** - Small pure moments

### Evening Deep (5 PM - 5 AM IST) - 17 Types

1. **Deep Emotional** - Heartbreak and introspection
2. **Nature/Universe** - Cosmic perspective
3. **Life Wisdom** - Philosophical observations
4. **One-Liner** - Powerful single-sentence quotes
5. **Hidden Truths** - Things nobody talks about
6. **Unpopular Opinion** - Honest controversial takes
7. **Childhood vs Now** - Nostalgic comparisons
8. **Self-Love & Boundaries** - Empowerment and worth
9. **Mental Health Real Talk** - Validation without toxic positivity
10. **Philosophical Light** - Karma, destiny, timing
11. **Overthinking/Anxiety** - Mental loop experiences
12. **Growth & Healing** - Transformation journey
13. **Late Night Thoughts** - 2 AM vulnerability
14. **Forgiveness & Letting Go** - Peace over being right
15. **Time Perspective** - Aging and fleeting moments
16. **Truth Bombs** - Harsh truths delivered kindly
17. **Travel/Wanderlust** - Exploration and adventure

### Content Distribution Strategy

- **Emotional Balance:** 35% deep, 30% relatable, 25% motivational, 10% funny
- **No Daily Repeats:** Each day covers different types
- **Weekly Variety:** All 33 types covered within 2-3 weeks
- **Anti-Cliché Rules:** No broken hearts, storms, rain, ocean metaphors
- **Gender-Neutral:** Universal relatability
- **Simple English:** Optimized for South Asian audience (90% India/Bangladesh/Nepal/Pakistan)

---

## 🏗️ Architecture

### System Design

The application follows a modular pipeline architecture with synchronized external storage:

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Gist Storage                         │
│                  (content_history.json)                         │
│           Tracks last 30 posts, prevents repetition             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
              ┌────────┴────────┐
              │                 │
    ┌─────────▼──────┐   ┌─────▼──────────┐
    │ GitHub Actions │   │  Render API    │
    │  (Automated)   │   │   (Manual)     │
    └────────┬───────┘   └────────┬───────┘
             │                    │
             └──────────┬─────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Core Processing Pipeline                      │
│                                                                 │
│  Content Selection → Quote Generation → Image Rendering         │
│       ↓                    ↓                    ↓               │
│  Smart Random       Gemini AI 3.6        Neon Effects           │
│  (33 types)         Simple English       PIL/Pillow             │
│                                                                 │
│                          ↓                                      │
│              Facebook Upload → Instagram Post                   │
│              (CDN URL sharing)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Execution Modes:**
   - `cron_autopilot.py` - GitHub Actions automated (primary)
   - `api.py` - Render API manual trigger (backup)
   - `main.py` - Local CLI testing

2. **Content Management:**
   - `content_schedule.py` - Smart randomization (33 types)
   - `PromptSelector.py` - Time-based prompt selection
   - `gist_storage.py` - External history synchronization

3. **Generation & Publishing:**
   - `QuoteGeneration.py` - Gemini AI integration
   - `ImageGeneration.py` - Neon visual rendering
   - `FBUpload.py` - Social media APIs

4. **Safety & Spacing:**
   - `check_last_post.py` - 2-hour minimum gap enforcement

---

## 📁 Project Structure

```
.
├── main.py                    # CLI orchestrator (manual testing)
├── cron_autopilot.py          # Automated scheduler script (GitHub Actions)
├── api.py                     # Minimal FastAPI server (Render hosting)
├── content_schedule.py        # Smart randomization engine (33 types)
├── PromptSelector.py          # Time-based prompt selector
├── QuoteGeneration.py         # AI content generation module
├── ImageGeneration.py         # Neon image rendering module
├── FBUpload.py               # Social media upload handlers
├── check_last_post.py        # 2-hour spacing enforcement
├── gist_storage.py           # GitHub Gist sync for history
├── create_gist_simple.py     # One-time Gist setup script
├── requirements.txt          # Python dependencies
├── .env                      # Environment configuration (GITIGNORED)
├── template.jpg              # Background image template
├── image.jpg                 # Generated output image (temp)
├── .github/
│   └── workflows/
│       └── daily-quote.yml   # GitHub Actions cron schedule (17 posts/day)
└── Montserrat/               # Font assets directory
    └── static/
        └── Montserrat-Light.ttf
```

---

## 🔧 Core Modules

### 1. `content_schedule.py` - Smart Content Type Selector

**Purpose:** Intelligently selects from 33 diverse content types based on time and recent history

**Smart Selection Algorithm:**

- **History Tracking:** Fetches last 30 posts from GitHub Gist
- **Weighted Randomization:**
  - Types not used recently: 3x weight
  - Types used 6-10 posts ago: 2x weight
  - Types used in last 5 posts: 1x weight
- **Time-Based Categories:** Morning (8 types), Afternoon (10 types), Evening (17 types)
- **Anti-Repetition:** Avoids using same type too frequently

**All 33 Content Types:**

**Morning Energy (5 AM - 12 PM IST):**
1. Motivational/Inspiring
2. Elder Wisdom
3. Gratitude/Mindful
4. Success/Hustle
5. Dreams & Ambitions
6. Life Lessons
7. Small Victories
8. Music & Art

**Afternoon Relatable (12 PM - 5 PM IST):**
1. Funny/Sassy
2. Bittersweet Relatable
3. Short Conversation
4. He/She Relationship
5. Pop Culture/Lyrics
6. Daily Struggle Humor
7. Food & Comfort
8. Social Commentary
9. Friendship & Bonds
10. Wholesome/Joy

**Evening Deep (5 PM - 5 AM IST):**
1. Deep Emotional
2. Nature/Universe
3. Life Wisdom
4. One-Liner
5. Hidden Truths
6. Unpopular Opinion
7. Childhood vs Now
8. Self-Love & Boundaries
9. Mental Health Real Talk
10. Philosophical Light
11. Overthinking/Anxiety
12. Growth & Healing
13. Late Night Thoughts
14. Forgiveness & Letting Go
15. Time Perspective
16. Truth Bombs
17. Travel/Wanderlust

### 2. `QuoteGeneration.py` - AI Content Generation

**Purpose:** Generates content using Google's Gemini AI based on selected content type

**Implementation Details:**

- **AI Model:** `gemini-2.0-flash-exp`
- **Input Source:** Reads generation instructions from `prompt.txt` + selected content type from `content_schedule.py`
- **Output:** Plain text content (quote, conversation, or message)
- **API Integration:** Uses `google-genai` SDK with authenticated requests

**Flow:**

```
content_schedule.py (selects type) → prompt.txt + type → Gemini AI → Generated Content
```

**Target Audience:**
- 90% South Asian (India, Bangladesh, Nepal, Pakistan)
- 18-34 years old
- 56% women, 44% men/unknown
- Primary cities: Kolkata, Dhaka, Kathmandu

---

### 3. `ImageGeneration.py` - Visual Content Renderer

**Purpose:** Transforms text quotes into styled neon-glow images

**Technical Specifications:**

- **Image Library:** PIL/Pillow
- **Font:** Montserrat-Light, 32px
- **Text Layout:**
  - Maximum 28 characters per line
  - Anti-orphan algorithm (prevents single-word last lines)
  - Center-aligned text positioning
- **Color Palette:**
  - Bulb Effect: `#FFDCEC`
  - Core Glow: `#FF2075`
  - Ambient Glow: `#610B2D`
- **Background:** Loads from `template.jpg`
- **Output:** Saves as `image.jpg` (overwrites)

**Processing Flow:**

```
Quote Text + template.jpg → Text Wrapping → Neon Effects → image.jpg
```

---

### 4. `FBUpload.py` - Social Media Publisher

**Purpose:** Handles uploads to Facebook and Instagram via Graph API

**Key Functions:**

#### `schedule_photo_after(image_path, page_id, access_token)`

- Uploads image to Facebook Page
- Retrieves CDN URL for cross-platform sharing
- Returns: Facebook CDN image URL

#### `post_to_instagram_from_fb_url(fb_image_url, ig_user_id, access_token)`

- Creates Instagram post using Facebook CDN URL
- Two-step process: container creation → publication
- Returns: Instagram post ID

**Current Configuration:**

- Immediate publishing (scheduled post code present but commented)
- Empty captions by default
- Uses Facebook Graph API v18.0+

**Publishing Flow:**

```
image.jpg → FB Upload → CDN URL → IG Container → IG Publish
```

---

### 5. `check_last_post.py` - Post Spacing Enforcer

**Purpose:** Prevents posting too frequently by checking time since last Facebook post

**Key Functions:**

#### `get_minutes_since_last_post()`
- Queries Facebook Graph API for most recent post timestamp
- Calculates minutes elapsed since last post
- Returns: Minutes as float, or None if error

#### `should_publish_new_post(min_hours=2)`
- Checks if enough time has passed (default: 2 hours)
- Returns: True if safe to publish, False otherwise
- **Safety First:** Returns False if unable to verify (prevents accidental spam)

**Why 2 Hours?**
- Prevents platform rate limiting
- Maintains organic posting appearance
- Works with 17 posts/day schedule (17 × 2hr = 34hr spread over 24hr with flexible timing)

### 6. `gist_storage.py` - External History Synchronization

**Purpose:** Stores content history in GitHub Gist for cross-environment synchronization

**Why GitHub Gist?**
- ✅ No commits to main repo (keeps git history clean)
- ✅ Synchronized between GitHub Actions and Render
- ✅ Free and reliable
- ✅ No third-party services or databases needed
- ✅ Simple REST API access

**Key Functions:**

#### `get_content_history()`
- Fetches `content_history.json` from GitHub Gist
- Returns: List of recent content types (last 30 posts)
- Gracefully handles network errors (returns empty list)

#### `save_content_history(history)`
- Updates gist with new history
- Automatically trims to last 30 posts
- Returns: True if successful, False otherwise

#### `add_to_history(content_type)`
- Convenience function: loads history → appends type → saves
- Used after each successful post

#### `create_gist()`
- One-time setup helper to create initial gist
- Creates private gist with empty history
- Returns gist ID to add to environment variables

**Storage Format:**
```json
[
  "DEEP_EMOTIONAL",
  "SHORT_CONVERSATION",
  "MOTIVATIONAL_INSPIRING",
  ...
]
```

**Environment Variables Required:**
- `CONTENT_HISTORY_GIST_ID` - Your gist ID
- `GITHUB_TOKEN` - GitHub personal access token with `gist` scope

### 7. `main.py` - CLI Orchestrator

**Purpose:** Manual single-run pipeline executor for testing

**Execution Sequence:**

1. Generate content via `QuoteGeneration.py`
2. Create neon image via `ImageGeneration.py`
3. Wait 10 seconds (stabilization buffer)
4. Upload to Facebook via `FBUpload.py`
5. Publish to Instagram using FB CDN URL

**Features:**

- Step-by-step console logging with emoji indicators
- Fail-fast error handling (stops on first error)
- Single execution model (no loops)
- Used for testing before deploying to automation

**Usage:**

```bash
python main.py
```

---

### 8. `cron_autopilot.py` - Automated Scheduler

**Purpose:** Production automation script executed by GitHub Actions

**Execution Sequence:**

1. Generate diverse content (randomly selects from 6 types)
2. Create neon image
3. Upload to Facebook and retrieve CDN URL
4. Publish to Instagram

**Features:**

- Minimal logging for clean GitHub Actions output
- Runs via GitHub Actions cron schedule
- **Schedule:** Every hour from 9:30 AM to 10:30 PM IST (14 posts/day)
- Handles errors gracefully without stopping the service

**GitHub Actions Configuration:**

```yaml
# .github/workflows/daily-quote.yml
schedule:
  # 17 posts per day with randomized minutes (organic appearance)
  - cron: '23 1 * * *'   # 6:53 AM IST
  - cron: '47 2 * * *'   # 8:17 AM IST
  - cron: '11 3 * * *'   # 8:41 AM IST
  - cron: '34 4 * * *'   # 10:04 AM IST
  - cron: '19 5 * * *'   # 10:49 AM IST
  - cron: '52 6 * * *'   # 12:22 PM IST
  - cron: '16 7 * * *'   # 12:46 PM IST
  - cron: '41 8 * * *'   # 2:11 PM IST
  - cron: '28 9 * * *'   # 2:58 PM IST
  - cron: '7 10 * * *'   # 3:37 PM IST
  - cron: '49 11 * * *'  # 5:19 PM IST
  - cron: '22 12 * * *'  # 5:52 PM IST
  - cron: '38 13 * * *'  # 7:08 PM IST
  - cron: '14 14 * * *'  # 7:44 PM IST
  - cron: '56 15 * * *'  # 9:26 PM IST
  - cron: '31 16 * * *'  # 10:01 PM IST
  - cron: '17 17 * * *'  # 10:47 PM IST
```

**Key Features:**
- Randomized minutes within each hour (looks organic, not automated)
- Spread across 16+ hours (6:53 AM - 10:47 PM IST)
- 2-hour spacing enforced by `check_last_post.py` (even if cron triggers more frequently)
- If a trigger is too soon after last post, it safely skips

---

### 9. `api.py` - Minimal REST API

**Purpose:** Lightweight API for health checks and manual triggers (hosted on Render)

**Framework:** FastAPI with Uvicorn ASGI server

**Endpoints:**

| Method | Endpoint     | Description                              |
| ------ | ------------ | ---------------------------------------- |
| `GET`  | `/health`    | Service health check with env validation |
| `GET`  | `/autopilot` | Manual trigger for full pipeline         |

**Note:** All other endpoints removed for simplicity. Primary automation runs via GitHub Actions, not API.

**Server Configuration:**

- **Host:** `0.0.0.0`
- **Port:** Environment variable `PORT` (Render compatibility)
- **Timeout:** 120 seconds
- **Logging:** INFO level with detailed step tracking

**Deployment:** Hosted on Render for uptime monitoring

**Usage:**

```bash
python api.py
```

---

## 🔐 Configuration & Security

### Environment Variables

All sensitive credentials are stored in `.env` file (excluded from version control).

**Required Variables:**

```bash
# Google Gemini AI
GEMINI_PROJECT_ID=your_google_cloud_project_id
GEMINI_API_KEY=your_gemini_api_key

# Facebook Page
PAGE_ID=your_facebook_page_id
PAGE_ACCESS_TOKEN=your_facebook_page_access_token
API_VERSION=v25.0

# Instagram Business Account
IG_USER_ID=your_instagram_business_account_id
IG_PAGE_ACCESS_TOKEN=your_instagram_page_access_token

# GitHub Gist for History Storage
GITHUB_TOKEN=your_github_personal_access_token
CONTENT_HISTORY_GIST_ID=your_gist_id

# Optional: ElevenLabs for future voice features
ELEVEN_LABS_1=your_elevenlabs_api_key
```

### Security Best Practices

⚠️ **IMPORTANT SECURITY NOTES:**

1. **Never commit `.env` file to version control**
2. **Rotate access tokens regularly** (Facebook tokens expire)
3. **Use environment-specific tokens** (dev/staging/production)
4. **Limit token permissions** to minimum required scopes
5. **Enable 2FA** on Facebook/Instagram accounts
6. **Monitor API usage** for anomalies
7. **Keep dependencies updated** (check `requirements.txt` regularly)

### Token Security

- Access tokens are loaded via `python-dotenv` at runtime
- No hardcoded credentials in source code
- API keys are passed as function parameters (not globals)
- Tokens are never logged or exposed in responses

---

## 📦 Dependencies

### Core Libraries

| Package         | Version | Purpose                         |
| --------------- | ------- | ------------------------------- |
| `fastapi`       | 0.140.0 | REST API framework              |
| `uvicorn`       | 0.51.0  | ASGI server                     |
| `pillow`        | 12.3.0  | Image manipulation              |
| `requests`      | 2.34.2  | HTTP client for API calls       |
| `google-genai`  | 2.14.0  | Google Gemini AI SDK            |
| `python-dotenv` | 1.2.2   | Environment variable management |
| `pydantic`      | 2.13.4  | Data validation                 |

### Installation

```bash
pip install -r requirements.txt
```

### Python Version

- **Required:** Python 3.8+
- **Recommended:** Python 3.10+

---

## 🎨 Content Strategy

### Content Distribution Strategy

**33 Content Types** organized by time and energy level:

| Time Period | Types | Purpose | Hours (IST) |
|-------------|-------|---------|-------------|
| **Morning Energy** | 8 types | Motivational start to day | 5 AM - 12 PM |
| **Afternoon Relatable** | 10 types | Peak engagement, relatable | 12 PM - 5 PM |
| **Evening Deep** | 17 types | Emotional depth, reflection | 5 PM - 5 AM |

### Smart Randomization Benefits

- **No Daily Repeats:** Each day covers different types
- **Weekly Variety:** All 33 types covered within 2-3 weeks
- **Prevents Fatigue:** Audience never sees repetitive content
- **Time-Appropriate:** Energy matches when people scroll
- **History Tracking:** GitHub Gist stores last 30 posts
- **Weighted Selection:** Unused types get 3x priority

### Emotional Balance (Automatic via Type Selection)

- **Morning:** 30% motivational, 40% wisdom, 30% gratitude
- **Afternoon:** 40% relatable, 30% funny, 30% wholesome
- **Evening:** 45% deep emotional, 30% wisdom, 25% growth

### Content Quality Rules

**Anti-Cliché Guidelines:**
- Avoid overused metaphors (broken hearts, storms, rain, oceans, stars)
- No forced poetry or flowery language
- Keep it conversational and authentic

**Inclusivity:**
- Gender-neutral by default (except "He/She Relationship" content type)
- Universal relatability across cultures
- Simple English optimized for South Asian audience

**Style:**
- Modern, conversational tone
- Short sentences for mobile reading
- Emotionally honest without toxic positivity

---

## 🚀 Deployment & Automation

### GitHub Actions (Primary Automation)

**Location:** `.github/workflows/daily-quote.yml`

**Schedule:** Cron expression `0 4-17 * * *`
- Runs every hour at minute :00
- Hours 4-17 UTC = 9:30 AM - 10:30 PM IST
- **14 posts per day** spread across 13 hours

**Workflow Steps:**
1. Checkout repository code
2. Set up Python 3.11
3. Install dependencies from `requirements.txt`
4. Run `cron_autopilot.py` with environment variables
5. Log output to GitHub Actions console

**Environment Variables (GitHub Secrets):**
- `GEMINI_API_KEY` - Google Gemini AI API key
- `GEMINI_PROJECT_ID` - Google Cloud project ID
- `PAGE_ID` - Facebook Page ID
- `PAGE_ACCESS_TOKEN` - Facebook Page Access Token
- `API_VERSION` - Facebook Graph API version (e.g., v25.0)
- `IG_USER_ID` - Instagram Business Account ID
- `IG_PAGE_ACCESS_TOKEN` - Instagram page access token
- `CONTENT_HISTORY_GIST_ID` - GitHub Gist ID for history storage
- `GITHUB_TOKEN` - Personal access token with `gist` scope (or use default Actions token)

**Manual Trigger:** Workflow can be manually triggered via GitHub UI (`workflow_dispatch`)

### Render Deployment (API Hosting)

**Purpose:** Hosts minimal API for health monitoring

**Service Type:** Web Service
**Region:** Singapore (Southeast Asia) - matches audience location
**Build Command:** `pip install -r requirements.txt`
**Start Command:** `python api.py`

**Environment Variables:** Same as GitHub Actions (configured in Render dashboard)

**Endpoints:**
- `https://quotify-1skc.onrender.com/health` - Health check
- `https://quotify-1skc.onrender.com/autopilot` - Manual trigger

**Note:** Render free tier sleeps after inactivity. GitHub Actions is the primary scheduler.

---

## 🎨 Visual Design

### Neon Aesthetic

- **Style:** Neon glow effect on dark background
- **Typography:** Montserrat-Light for modern, clean aesthetic
- **Layout:** Center-aligned text with anti-orphan line breaking
- **Color Palette:**
  - Bulb Effect: `#FFDCEC` (soft pink)
  - Core Glow: `#FF2075` (hot pink)
  - Ambient Glow: `#610B2D` (deep magenta)
- **Brand Identity:** "Aesthetic Vibes" - lost souls finding words that feel like home

### Technical Design Decisions

- **Modularity:** Each component is independently testable
- **Error Handling:** Graceful failures with detailed logging
- **File I/O:** Direct file system writes (no database)
- **Caption Strategy:** Empty by default to maximize visual focus
- **CDN Strategy:** Upload to FB first, reuse URL for IG (API efficiency)
- **Scheduling:** GitHub Actions cron (free, reliable, no server needed)

---

## 🔍 Asset Requirements

### Required Files

1. **`template.jpg`** (Project root)
   - Purpose: Background image for quote rendering
   - Format: JPEG
   - Recommended: Dark background, high contrast

2. **`prompt.txt`** (Project root)
   - Purpose: Instructions for AI quote generation
   - Format: Plain text
   - Content: Prompt engineering for desired quote style

3. **`Montserrat/static/Montserrat-Light.ttf`**
   - Purpose: Font for text rendering
   - License: SIL Open Font License
   - Alternative: Any TTF font (update path in code)

### Generated Files

- **`image.jpg`** - Temporary output (overwritten each run)
- **`.env`** - User-created configuration file

---

## 🛠️ Development & Testing

### Local Testing

```bash
# Test full pipeline once
python main.py

# Test API endpoints
python api.py
# Visit http://localhost:8000/docs for Swagger UI

# Test automation script (what GitHub Actions runs)
python cron_autopilot.py
```

### Error Handling Strategy

- **CLI mode** (`main.py`): Immediate exit on any error with clear messaging
- **API mode** (`api.py`): HTTP status codes with detailed error messages
- **Automation mode** (`cron_autopilot.py`): Graceful failures, logs errors but continues service
- **Logging:** INFO level with step-by-step progress tracking

### Current Limitations

- No content moderation built-in (relies on Gemini AI's safety filters)
- No analytics tracking (relies on native Facebook/Instagram insights)
- No database (uses GitHub Gist for history only)
- No A/B testing framework
- Caption support exists but unused (empty by default)
- ElevenLabs API key present but voice features not implemented yet

### Monitoring

- **GitHub Actions logs:** Check workflow run history for errors
- **Render logs:** Monitor API health and uptime
- **Facebook/Instagram Insights:** Track engagement metrics

---

## 📄 License & Attribution

### Privacy Policy

**Important:** This project collects and processes data through third-party services. Please review our Privacy Policy:

🔒 **Privacy Policy:** https://www.privacypolicies.com/live/30db9e31-69f7-4904-8d66-bf4bdbc407e5

By using this application, you agree to:
- Our data collection and usage practices
- Third-party service terms (Google Gemini AI, Facebook/Instagram APIs)
- The privacy policies of integrated platforms

### Font License

- **Montserrat Font:** SIL Open Font License (OFL)
- See `Montserrat/OFL.txt` for details

### External Services

- Google Gemini AI API (Terms apply)
- Facebook Graph API (Platform Policy applies)
- Instagram Graph API (Platform Policy applies)

---

## ⚡ Quick Start Guide

### Prerequisites

- [ ] Python 3.8+ installed
- [ ] Git installed
- [ ] GitHub account (for Actions automation)
- [ ] Facebook Page with Instagram Business Account linked
- [ ] Google Gemini API key

### Local Setup

1. **Clone repository:**
   ```bash
   git clone <your-repo-url>
   cd Quotify
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file:**
   ```bash
   GEMINI_PROJECT_ID=your_google_cloud_project_id
   GEMINI_API_KEY=your_gemini_api_key
   PAGE_ID=your_facebook_page_id
   PAGE_ACCESS_TOKEN=your_facebook_page_token
   API_VERSION=v25.0
   IG_USER_ID=your_instagram_business_id
   IG_PAGE_ACCESS_TOKEN=your_instagram_token
   GITHUB_TOKEN=your_github_token
   CONTENT_HISTORY_GIST_ID=your_gist_id
   ```

4. **Add required assets:**
   - Place `template.jpg` in project root
   - Verify `prompt.txt` exists
   - Verify font: `Montserrat/static/Montserrat-Light.ttf`

5. **Test locally:**
   ```bash
   python main.py
   ```

### GitHub Gist Setup (One-Time, 5 minutes)

**Step 1: Create GitHub Personal Access Token**

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name it: `Aesthetic Vibes Content History`
4. Select scopes: ✅ `gist` (Create gists)
5. Click "Generate token" and copy it (you won't see it again!)

**Step 2: Create the Gist**

Run locally:
```bash
export GITHUB_TOKEN="your_token_here"
python3 create_gist_simple.py
```

This will output:
```
✅ Gist created successfully!
📋 GIST ID: abc123def456ghi789
🔗 URL: https://gist.github.com/yourusername/abc123def456ghi789
```

**Step 3: Verify Setup**

Test locally:
```bash
export CONTENT_HISTORY_GIST_ID="your_gist_id"
export GITHUB_TOKEN="your_token"
python3 gist_storage.py
```

Should show:
```
✅ History loaded: 0 posts
✅ History saved to gist
✅ Test cleanup complete
```

### GitHub Actions Setup

1. **Add secrets to GitHub repository:**
   - Go to: Settings → Secrets and variables → Actions
   - Add all environment variables as secrets (including `CONTENT_HISTORY_GIST_ID` and `GITHUB_TOKEN`)

2. **Enable GitHub Actions:**
   - Go to: Actions tab
   - Enable workflows if disabled

3. **Manual test run:**
   - Go to: Actions → Daily Quote Autopilot
   - Click "Run workflow" → "Run workflow"
   - Check logs for success

4. **Automated execution:**
   - Workflow runs automatically 17 times per day (6:53 AM - 10:47 PM IST)
   - 2-hour minimum spacing enforced automatically
   - No further action needed

**How It Works:**
- GitHub Actions runs on cron schedule (17 triggers/day)
- Each run checks if 2 hours passed since last post
- If yes: selects content type → generates → posts → updates Gist history
- If no: skips safely (no duplicate posts)
- History synced via Gist (no git commits needed)

### Render Deployment (Optional)

1. Create new Web Service on Render
2. Connect GitHub repository
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python api.py`
   - Environment: Add all 5 variables
   - Region: Singapore (for South Asian audience)

---

## 📊 Page Performance

### Current Metrics (as of Jan 2026)

- **Followers:** 55,000
- **Audience:** 90% South Asian (India, Bangladesh, Nepal, Pakistan)
- **Age:** 56% (25-34), 36% (18-24)
- **Gender:** 56% women, 44% men/unknown
- **Top Cities:** Kolkata, Dhaka, Kathmandu
- **Page Status:** Revival phase after period of inactivity

### Content Strategy

- **Goal:** Revive engagement and regain active followers
- **Approach:** 14 posts/day with diverse content types
- **Testing Phase:** First 2 weeks to identify top-performing content
- **Optimization:** Adjust content type ratios based on engagement data

---

**Last Updated:** 2026-01-26  
**Python Version:** 3.8+  
**Page:** Aesthetic Vibes (Instagram/Facebook)  
**Maintained By:** Priyom Saha

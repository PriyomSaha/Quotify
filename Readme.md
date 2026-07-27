# Aesthetic Vibes - Automated Quote Publishing System

## 📋 Project Overview

**"We are not a poet, Just a lost soul finding combination of words to bring you home"**

An automated content generation and publishing system for the Instagram/Facebook page "Aesthetic Vibes" (55K followers). The system creates AI-generated diverse content (emotional quotes, conversations, motivational messages), renders them as neon-styled images, and automatically publishes to social media platforms.

**Pipeline Flow:** AI Content Generation → Neon Image Creation → Facebook Upload → Instagram Publishing

**Posting Schedule:** 14 posts per day, every hour from 9:30 AM to 10:30 PM IST (Indian Standard Time)

---

## 🏗️ Architecture

### System Design

The application follows a modular pipeline architecture with three execution modes:

1. **CLI Mode** (`main.py`) - Manual single-run execution for testing
2. **API Mode** (`api.py`) - Minimal REST API for Render health checks and manual triggers
3. **Automated Mode** (`cron_autopilot.py`) - GitHub Actions scheduled execution (primary mode)

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Execution Modes                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   main.py    │  │   api.py     │  │ cron_autopilot.py    │  │
│  │ (Manual CLI) │  │ (Render API) │  │ (GitHub Actions)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Core Processing Modules                       │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ QuoteGeneration  │  │ ImageGeneration  │                    │
│  │                  │  │                  │                    │
│  │ - Gemini AI SDK  │  │ - PIL/Pillow     │                    │
│  │ - Dynamic Prompt │  │ - Neon Effects   │                    │
│  │ - 6 Content Types│  │ - Text Wrapping  │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                 │
│  ┌──────────────────────────────────────┐                      │
│  │          FBUpload                    │                      │
│  │                                      │                      │
│  │ - Facebook Graph API Integration     │                      │
│  │ - Instagram Graph API Integration    │                      │
│  │ - CDN URL retrieval                  │                      │
│  └──────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                          │
│                                                                 │
│  [ Google Gemini AI ] [ Facebook API ] [ Instagram API ]        │
│  [ GitHub Actions (Scheduler) ] [ Render (API Host) ]           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
.
├── main.py                    # CLI orchestrator (manual testing)
├── cron_autopilot.py          # Automated scheduler script (GitHub Actions)
├── api.py                     # Minimal FastAPI server (Render hosting)
├── QuoteGeneration.py         # AI content generation module
├── ImageGeneration.py         # Neon image rendering module
├── FBUpload.py               # Social media upload handlers
├── PageAccessTokenGenerate.py # Token generation utility
├── requirements.txt          # Python dependencies
├── .env                      # Environment configuration (GITIGNORED)
├── prompt.txt                # AI generation prompt with 6 content types
├── template.jpg              # Background image template
├── image.jpg                 # Generated output image (temp)
├── .github/
│   └── workflows/
│       └── daily-quote.yml   # GitHub Actions cron schedule
└── Montserrat/               # Font assets directory
    └── static/
        └── Montserrat-Light.ttf
```

---

## 🔧 Core Modules

### 1. `QuoteGeneration.py` - AI Content Generation

**Purpose:** Generates diverse content types using Google's Gemini AI

**Implementation Details:**

- **AI Model:** `gemini-2.0-flash-exp`
- **Input Source:** Reads generation instructions from `prompt.txt`
- **Output:** Plain text content (quote, conversation, or message)
- **API Integration:** Uses `google-genai` SDK with authenticated requests

**Content Types Generated (6 types with weighted probabilities):**

1. **Deep Emotional Quotes (35%)** - Heartbreak, nostalgia, introspection
2. **Short Conversations (25%)** - Relatable dialogue between two people
3. **Bittersweet Moments (20%)** - Oddly-specific universal experiences
4. **One-Liners (10%)** - Punchy single-sentence quotes
5. **Motivational/Healing (5%)** - Grounded encouragement
6. **Wholesome/Joy (5%)** - Light, comforting moments

**Flow:**

```
prompt.txt → Gemini AI (random content type selection) → Generated Content
```

**Target Audience:**
- 90% South Asian (India, Bangladesh, Nepal, Pakistan)
- 18-34 years old
- 56% women, 44% men/unknown
- Primary cities: Kolkata, Dhaka, Kathmandu

---

### 2. `ImageGeneration.py` - Visual Content Renderer

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

### 3. `FBUpload.py` - Social Media Publisher

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

### 4. `main.py` - CLI Orchestrator

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

### 5. `cron_autopilot.py` - Automated Scheduler

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
  - cron: '0 4-17 * * *'  # Runs hours 4-17 UTC = 9:30 AM - 10:30 PM IST
```

**Posting Times (IST):**
- 9:30 AM, 10:30 AM, 11:30 AM, 12:30 PM, 1:30 PM, 2:30 PM, 3:30 PM
- 4:30 PM, 5:30 PM, 6:30 PM, 7:30 PM, 8:30 PM, 9:30 PM, 10:30 PM

---

### 6. `api.py` - Minimal REST API

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
PAGE_ID=<your_facebook_page_id>
PAGE_ACCESS_TOKEN=<your_facebook_access_token>
API_VERSION=<facebook_graph_api_version>
IG_USER_ID=<your_instagram_business_account_id>
GEMINI_API_KEY=<your_google_ai_api_key>
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

### Content Type Distribution

The `prompt.txt` file defines 6 content types with weighted probabilities to ensure variety:

| Content Type          | Probability | Purpose                               | Example                                    |
| --------------------- | ----------- | ------------------------------------- | ------------------------------------------ |
| Deep Emotional Quote  | 35%         | Core brand strength - emotional depth | "We keep old texts like pressed flowers"  |
| Short Conversation    | 25%         | High engagement - tag potential       | "A: Still awake? / B: Always"             |
| Bittersweet Moment    | 20%         | Viral relatability                    | "Scrolling to find that one photo..."     |
| One-Liner             | 10%         | High shareability                     | "Some goodbyes happen in silence"         |
| Motivational/Healing  | 5%          | Balance the sadness                   | "Healing isn't linear, and that's okay"   |
| Wholesome/Joy         | 5%          | Unexpected delight                    | "When someone remembers the small thing" |

### Tone Balance

- **35%** - Deep emotional/sad (proven audience preference)
- **25%** - Bittersweet/nostalgic (relatable)
- **20%** - Everyday relatable moments (engagement)
- **10%** - Motivational/healing (balance)
- **10%** - Light/wholesome (variety)

### Anti-Cliché Rules

**Banned metaphors:** broken hearts, storms, rain, oceans, stars, sunsets, mirrors, scars, echoes, fading photographs

**Gender-neutral:** No he/she, boyfriend/girlfriend, mother/father references

**Modern language:** Conversational, authentic, not poetic-for-the-sake-of-poetry

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
- `PAGE_ID` - Facebook Page ID
- `PAGE_ACCESS_TOKEN` - Facebook Page Access Token
- `API_VERSION` - Facebook Graph API version
- `IG_USER_ID` - Instagram Business Account ID

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

- No content moderation built-in
- No analytics tracking (relies on native platform insights)
- No database persistence (stateless execution)
- No A/B testing framework
- Caption support exists but unused (empty by default)

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
   GEMINI_API_KEY=your_gemini_api_key
   PAGE_ID=your_facebook_page_id
   PAGE_ACCESS_TOKEN=your_facebook_page_token
   API_VERSION=v18.0
   IG_USER_ID=your_instagram_business_id
   ```

4. **Add required assets:**
   - Place `template.jpg` in project root
   - Verify `prompt.txt` exists
   - Verify font: `Montserrat/static/Montserrat-Light.ttf`

5. **Test locally:**
   ```bash
   python main.py
   ```

### GitHub Actions Setup

1. **Add secrets to GitHub repository:**
   - Go to: Settings → Secrets and variables → Actions
   - Add all 5 environment variables as secrets

2. **Enable GitHub Actions:**
   - Go to: Actions tab
   - Enable workflows if disabled

3. **Manual test run:**
   - Go to: Actions → Daily Quote Autopilot
   - Click "Run workflow" → "Run workflow"
   - Check logs for success

4. **Automated execution:**
   - Workflow runs automatically every hour (9:30 AM - 10:30 PM IST)
   - No further action needed

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

# Social Media Automation Pipeline - Project Documentation

## 📋 Project Overview

An automated content generation and publishing system that creates AI-generated motivational quotes, renders them as neon-styled images, and publishes them to Facebook and Instagram social media platforms.

**Pipeline Flow:** AI Quote Generation → Neon Image Creation → Facebook Upload → Instagram Publishing

---

## 🏗️ Architecture

### System Design

The application follows a modular pipeline architecture with two execution modes:

1. **CLI Mode** (`main.py`) - Sequential single-run execution
2. **API Mode** (`api.py`) - RESTful web service with independent endpoints

### Component Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Entry Points                        │
│  ┌──────────────┐              ┌──────────────┐        │
│  │   main.py    │              │    api.py    │        │
│  │ (CLI Runner) │              │ (REST API)   │        │
│  └──────────────┘              └──────────────┘        │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────┐
│              Core Processing Modules                  │
│                                                       │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ QuoteGeneration  │  │ ImageGeneration  │           │
│  │                  │  │                  │           │
│  │ - Gemini AI SDK  │  │ - PIL/Pillow     │           │
│  │ - Text Gen       │  │ - Neon Effects   │           │
│  └──────────────────┘  └──────────────────┘           │
│                                                       │
│  ┌──────────────────────────────────────┐             │
│  │          FBUpload                    │             │
│  │                                      │             │
│  │ - Facebook Graph API Integration     │             │
│  │ - Instagram Graph API Integration    │             │
│  └──────────────────────────────────────┘             │
└───────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              External Services                          │
│                                                         │
│  [ Google Gemini AI ] [ Facebook ] [ Instagram ]        │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
.
├── main.py                    # CLI orchestrator (single-run)
├── api.py                     # FastAPI REST server
├── QuoteGeneration.py         # AI quote generation module
├── ImageGeneration.py         # Neon image rendering module
├── FBUpload.py               # Social media upload handlers
├── PageAccessTokenGenerate.py # Token generation utility
├── requirements.txt          # Python dependencies
├── .env                      # Environment configuration (GITIGNORED)
├── prompt.txt                # AI generation prompt template
├── template.jpg              # Background image template
├── image.jpg                 # Generated output image (temp)
└── Montserrat/               # Font assets directory
    └── static/
        └── Montserrat-Light.ttf
```

---

## 🔧 Core Modules

### 1. `QuoteGeneration.py` - AI Content Generation

**Purpose:** Generates motivational quotes using Google's Gemini AI

**Implementation Details:**

- **AI Model:** `gemini-3.6-flash`
- **Input Source:** Reads generation instructions from `prompt.txt`
- **Output:** Plain text quote string
- **API Integration:** Uses `google-genai` SDK with authenticated requests

**Flow:**

```
prompt.txt → Gemini API → Generated Quote Text
```

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

**Purpose:** Single-run command-line pipeline executor

**Execution Sequence:**

1. Generate quote via `QuoteGeneration.py`
2. Create neon image via `ImageGeneration.py`
3. Wait 10 seconds (stabilization buffer)
4. Upload to Facebook via `FBUpload.py`
5. Publish to Instagram using FB CDN URL

**Features:**

- Step-by-step console logging with emoji indicators
- Fail-fast error handling (stops on first error)
- Single execution model (no loops)

**Usage:**

```bash
python main.py
```

---

### 5. `api.py` - REST API Server

**Purpose:** Exposes pipeline components as independent HTTP endpoints

**Framework:** FastAPI with Uvicorn ASGI server

**Endpoints:**

| Method | Endpoint         | Description            | Timeout |
| ------ | ---------------- | ---------------------- | ------- |
| `GET`  | `/`              | Health check / welcome | -       |
| `GET`  | `/health`        | Service status         | -       |
| `GET`  | `/generatequote` | Generate AI quote      | 120s    |
| `POST` | `/generateimage` | Create neon image      | 120s    |
| `POST` | `/fbupload`      | Upload to Facebook     | 120s    |
| `POST` | `/igupload`      | Publish to Instagram   | 120s    |

**Request/Response Models:**

- Type-validated with Pydantic schemas
- JSON request bodies for POST endpoints
- Structured error responses

**Server Configuration:**

- **Host:** `0.0.0.0`
- **Port:** `8000`
- **Documentation:** Auto-generated at `/docs` (Swagger UI)

**Usage:**

```bash
python api.py
```

Access interactive docs at: `http://localhost:8000/docs`

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

## 🎨 Design Decisions

### Visual Design

- **Style:** Neon glow effect on dark background
- **Typography:** Montserrat-Light for modern, clean aesthetic
- **Layout:** Center-aligned text with anti-orphan line breaking
- **Color Theory:** Pink/magenta neon for visibility and brand appeal

### Technical Decisions

- **Modularity:** Each component is independently testable
- **Error Handling:** Fail-fast in CLI, detailed responses in API
- **File I/O:** Direct file system writes (no database)
- **Caption Strategy:** Empty by default to maximize visual focus
- **CDN Strategy:** Upload to FB first, reuse URL for IG (efficiency)

### API Design

- **RESTful:** Resource-oriented endpoints
- **Timeouts:** 2-minute limits prevent hanging requests
- **Documentation:** Auto-generated OpenAPI schema
- **Validation:** Pydantic models ensure type safety

---

## 🚀 Usage Guide

### CLI Mode (One-Time Execution)

```bash
# Run complete pipeline once
python main.py
```

**Output:** Console logs for each step, final image posted to both platforms

### API Mode (Persistent Service)

```bash
# Start API server
python api.py
```

**Testing Endpoints:**

```bash
# Generate quote
curl http://localhost:8000/generatequote

# Create image
curl -X POST http://localhost:8000/generateimage \
  -H "Content-Type: application/json" \
  -d '{"quote": "Your inspirational text here"}'

# Upload to Facebook
curl -X POST http://localhost:8000/fbupload \
  -H "Content-Type: application/json" \
  -d '{"image_path": "image.jpg"}'

# Publish to Instagram
curl -X POST http://localhost:8000/igupload \
  -H "Content-Type: application/json" \
  -d '{"fb_image_url": "https://..."}'
```

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

## 🛠️ Development Notes

### Error Handling Strategy

- CLI mode: Immediate exit on any error with clear messaging
- API mode: HTTP status codes with descriptive error messages
- No automatic retries (explicit design choice)

### Current Limitations

- Single image generation per execution
- No content moderation built-in
- No post scheduling (immediate publish only)
- No analytics tracking
- No database persistence

### Future Enhancement Opportunities

- Batch processing support
- Scheduled posting queue
- Content approval workflow
- Analytics dashboard
- Template customization API
- Multi-platform expansion (Twitter, LinkedIn)

---

## 📄 License & Attribution

### Font License

- **Montserrat Font:** SIL Open Font License (OFL)
- See `Montserrat/OFL.txt` for details

### External Services

- Google Gemini AI API (Terms apply)
- Facebook Graph API (Platform Policy applies)
- Instagram Graph API (Platform Policy applies)

---

## ⚡ Quick Start Checklist

- [ ] Install Python 3.8+
- [ ] Clone repository
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file with required credentials
- [ ] Add `template.jpg` to project root
- [ ] Create/verify `prompt.txt` exists
- [ ] Test: `python main.py` or `python api.py`
- [ ] Verify font path: `Montserrat/static/Montserrat-Light.ttf`

---

**Last Updated:** 2026-07-25  
**Python Version:** 3.8+  
**Maintained By:** Project Team

# Project Brief: Aesthetic Vibes Content Automation

## Overview
Aesthetic Vibes is an automated social media content generation and publishing system for the Instagram page `@aesthetic_o_vibes` and Facebook page `AesthaticsVibes`. The system generates emotional quotes, aesthetic quote images, and cinematic reels with voiceover and subtitles, then publishes them to Facebook and Instagram on a smart schedule.

## Core Mission
Share emotional quotes, deep thoughts, relatable conversations, life wisdom, and cinematic reels for "lost souls finding their way home through words."

## Target Audience
- 90% South Asian (India, Bangladesh, Nepal, Pakistan)
- Ages 18-34
- Mostly women
- Content in simple English that Indian audiences can easily understand

## Primary Capabilities
1. **AI Quote Generation** - Uses Gemini to generate diverse quote content across 35 content types
2. **Aesthetic Quote Image Creation** - Renders quotes onto neon-style images using PIL
3. **Cinematic Reel Generation** - Creates 9:16 reels with AI-generated story, images, voiceover, and subtitles
4. **Social Media Publishing** - Uploads to Facebook and Instagram via Meta Graph API
5. **Smart Scheduling** - IST-based weekly posting windows with anti-overlap locking
6. **Event-Aware Content** - Date-based content enhancement for Indian festivals and holidays

## Key Entry Points
| Entry Point | Purpose |
|---|---|
| `.github/workflows/quote-scheduler.yml` | Scheduled quote publishing (every 5 min) |
| `.github/workflows/reel-scheduler.yml` | Scheduled reel generation/publishing (every 5 min) |
| `api.py` | FastAPI service for health checks, manual triggers, and shared reel execution |
| `Reels_main.py` | CLI/main reel pipeline |
| `smart_scheduler.py` | Shared scheduler decision engine and locking |
| `Photos_main.py` | Manual quote-to-social pipeline |
| `cron_autopilot.py` | Direct cron job script for quote flow |

## Deployment
- **GitHub Actions**: Primary scheduler for both quote and reel workflows
- **Render**: FastAPI service for health checks and manual triggers
- **GitHub Gist**: State storage for scheduler state and content history
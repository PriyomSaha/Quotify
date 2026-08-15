# Product Context: Aesthetic Vibes

## Why This Project Exists
Aesthetic Vibes exists to provide a fully automated, hands-off social media presence that consistently publishes emotionally resonant content. The system eliminates the need for manual content creation, design, scheduling, and posting by automating the entire pipeline from AI generation to social media publication.

## Problems It Solves
1. **Content Consistency** - Maintains a regular posting schedule without human intervention
2. **Content Diversity** - Uses 35 distinct content types with smart anti-repetition weighting
3. **Time Zone Optimization** - Posts during IST-based engagement windows (morning, afternoon, evening, prime time)
4. **Cross-Platform Publishing** - Publishes to both Facebook and Instagram from a single pipeline
5. **Event Relevance** - Automatically enhances content for Indian festivals, holidays, and cultural events
6. **Resource Efficiency** - Uses GitHub Actions (free) and Render (free tier) for deployment

## User Experience Goals
- **For Followers**: Consistent, emotionally resonant, culturally relevant content that feels personal and shareable
- **For Operators**: Zero-touch automation with reliable failure recovery and state synchronization
- **For Developers**: Clear separation of concerns with modular, testable components

## Key User Journeys
1. **Quote Pipeline**: Scheduler detects window → Gemini generates quote → PIL renders neon image → Facebook upload → Instagram publish → state updated
2. **Reel Pipeline**: Scheduler detects window → Gemini generates story → Cloudflare generates 6 scene images → Edge-TTS generates voiceover → MoviePy composes video with subtitles → Cloudinary hosts video → Facebook/Instagram upload → cleanup
3. **Event Mode**: Calendar detects special date → content prompts become event-aware → captions include event wishes/hashtags → visuals use event-specific cues

## Core Value Proposition
"Set it and forget it" social media automation that produces culturally-aware, emotionally-resonant content for a South Asian audience, running entirely on free infrastructure.

## Success Metrics
- Consistent daily posting (2 quotes + 3 reels per day)
- Content variety across all 35 content types
- No duplicate posts or overlapping jobs
- Successful cross-platform publishing (both Facebook and Instagram)
- Event-aware content during cultural celebrations
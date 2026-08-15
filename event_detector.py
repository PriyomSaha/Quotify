"""
event_detector.py

Date-aware content enhancement for Aesthetic Vibes.

This module adds an optional event layer on top of the existing random content
logic. If today matches an event in content_calendar.json, quote/reel prompts
and captions can become event-aware. If no event matches, the existing random
logic continues unchanged.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

IST = timezone(timedelta(hours=5, minutes=30))
CALENDAR_FILE = Path(__file__).resolve().parent / "content_calendar.json"

PRIORITY_WEIGHT = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

TEST_DATE_ENV = "EVENT_TEST_DATE"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Production installs include python-dotenv, but keep this module importable
    # in minimal local environments too.
    pass


def parse_test_date(date_text: str) -> datetime:
    """
    Parse a test date string into an IST datetime.

    Supported formats:
    - YYYY-MM-DD
    - YYYY-MM-DD HH:MM
    - YYYY-MM-DDTHH:MM
    """
    cleaned = date_text.strip()
    formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"]

    for date_format in formats:
        try:
            parsed = datetime.strptime(cleaned, date_format)
            return parsed.replace(tzinfo=IST)
        except ValueError:
            continue

    raise ValueError(
        f"Invalid test date '{date_text}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM."
    )


def get_effective_now(now: Optional[datetime] = None) -> datetime:
    """
    Return the date used for event detection.

    Priority:
    1. Explicit now parameter
    2. EVENT_TEST_DATE environment variable
    3. Current date/time in IST
    """
    if now:
        return now.astimezone(IST)

    test_date = os.getenv(TEST_DATE_ENV, "").strip()
    if test_date:
        effective_now = parse_test_date(test_date)
        print(f"🧪 Event test date active: {effective_now.strftime('%Y-%m-%d %H:%M %Z')}")
        return effective_now

    return datetime.now(IST)


def set_event_test_date(date_text: Optional[str]) -> None:
    """Set or clear EVENT_TEST_DATE for the current Python process."""
    if date_text:
        # Validate before storing.
        parse_test_date(date_text)
        os.environ[TEST_DATE_ENV] = date_text
        print(f"🧪 EVENT_TEST_DATE set to {date_text}")
    else:
        os.environ.pop(TEST_DATE_ENV, None)


def _load_calendar() -> Dict[str, Any]:
    if not CALENDAR_FILE.exists():
        return {"fixed_events": {}, "dated_events": {}}

    try:
        with CALENDAR_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as exc:
        print(f"⚠️ Could not read event calendar: {exc}")
        return {"fixed_events": {}, "dated_events": {}}

    return {
        "fixed_events": data.get("fixed_events", {}) or {},
        "dated_events": data.get("dated_events", {}) or {},
    }


def _event_matches(event_date: datetime, today: datetime, event: Dict[str, Any]) -> bool:
    active_before = int(event.get("active_before_days", 0) or 0)
    active_after = int(event.get("active_after_days", 0) or 0)

    start_date = event_date.date() - timedelta(days=active_before)
    end_date = event_date.date() + timedelta(days=active_after)

    return start_date <= today.date() <= end_date


def _with_runtime_fields(
    event: Dict[str, Any],
    event_date: datetime,
    today: datetime,
    date_key: str,
    source: str,
) -> Dict[str, Any]:
    enriched = dict(event)
    enriched["date_key"] = date_key
    enriched["source"] = source
    enriched["event_date"] = event_date.date().isoformat()
    enriched["days_until"] = (event_date.date() - today.date()).days
    enriched["is_exact_date"] = event_date.date() == today.date()
    return enriched


def get_active_events(now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Return all calendar events active for today in IST."""
    today = get_effective_now(now)
    calendar = _load_calendar()
    events: List[Dict[str, Any]] = []

    for date_key, event in calendar["fixed_events"].items():
        try:
            month, day = map(int, date_key.split("-"))
            event_date = today.replace(month=month, day=day)
        except Exception:
            print(f"⚠️ Invalid fixed event date key: {date_key}")
            continue

        if _event_matches(event_date, today, event):
            events.append(_with_runtime_fields(event, event_date, today, date_key, "fixed_events"))

    for date_key, event in calendar["dated_events"].items():
        try:
            event_date = datetime.strptime(date_key, "%Y-%m-%d").replace(tzinfo=IST)
        except Exception:
            print(f"⚠️ Invalid dated event date key: {date_key}")
            continue

        if _event_matches(event_date, today, event):
            events.append(_with_runtime_fields(event, event_date, today, date_key, "dated_events"))

    return sorted(
        events,
        key=lambda item: (
            PRIORITY_WEIGHT.get(str(item.get("priority", "low")).lower(), 1),
            1 if item.get("is_exact_date") else 0,
            -abs(int(item.get("days_until", 0))),
        ),
        reverse=True,
    )


def get_today_event(now: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Return the highest-priority active event for today, or None."""
    events = get_active_events(now=now)
    if not events:
        return None

    event = events[0]
    print(f"🎉 Event mode active: {event.get('name')} ({event.get('date_key')})")
    return event


def get_event_wish(event: Optional[Dict[str, Any]]) -> str:
    """Return a short event wish for social captions."""
    if not event:
        return ""

    custom_wish = str(event.get("wish", "") or "").strip()
    if custom_wish:
        return custom_wish

    name = str(event.get("name", "") or "").strip()
    if not name:
        return ""

    return f"Happy {name}"


def _event_iconic_visuals(event: Dict[str, Any]) -> List[str]:
    """Return a prioritized list of event-signature visual cues and iconic elements."""
    event_name = str(event.get("name", "")).lower()
    mapped = {
        "independence day": [
            "Indian tricolor flag",
            "India Gate or iconic Indian monument",
            "flag hoisting scene",
            "patriotic crowd with tricolor energy",
            "sunrise over India with saffron-white-green tones",
        ],
        "republic day": [
            "Indian tricolor flag",
            "Republic Day parade",
            "India Gate and patriotic crowd",
            "constitution and democratic pride",
            "red fort or parade formation with national colors",
        ],
        "gandhi jayanti": [
            "peaceful Indian village or simple morning scene",
            "spinning wheel / charkha symbol",
            "truth and non-violence imagery",
            "quiet dignity and simplicity",
        ],
        "teachers' day": [
            "classroom or teacher-student learning scene",
            "chalkboard, notebook, pen, or desk",
            "gratitude for guidance",
        ],
        "mothers' day": [
            "old kitchen or family home morning scene",
            "mother's hands preparing food",
            "family warmth and care",
        ],
        "fathers' day": [
            "father's everyday gestures",
            "wristwatch, keys, morning tea, quiet support",
            "family bond and protection",
        ],
        "friendship day": [
            "school or college friends",
            "old group photo or shared street scene",
            "nostalgic childhood friendship moments",
        ],
        "raksha bandhan": [
            "rakhi thread",
            "siblings together",
            "family celebration scene",
        ],
        "valentine's day": [
            "old handwritten note",
            "two cups of tea",
            "rainy window or empty bench",
            "love and distance imagery",
        ],
    }

    visual_cues = []
    for name_key, cues in mapped.items():
        if name_key in event_name:
            visual_cues.extend(cues)

    visual_hints = event.get("visual_hints", []) or []
    if visual_hints:
        visual_cues.extend([str(v) for v in visual_hints if str(v).strip()])

    deduped = []
    seen = set()
    for cue in visual_cues:
        if cue not in seen:
            seen.add(cue)
            deduped.append(cue)
    return deduped[:10]


def build_event_identity_instruction(event: Dict[str, Any]) -> str:
    """Add strong event identity guidance without affecting normal non-event days."""
    event_name = str(event.get("name", "special occasion")).strip()
    visual_cues = _event_iconic_visuals(event)
    visual_text = ", ".join(visual_cues) if visual_cues else "iconic cues tied to this occasion"

    return f"""

EVENT IDENTITY RULE
- The content must clearly represent {event_name} and should be unmistakably about this occasion.
- It must include iconic elements strongly associated with {event_name} rather than generic abstract mood imagery.
- The visuals/text should clearly say what this event is famous for.
- Use recognizable cues such as: {visual_text}.
- Avoid generic scenes that could belong to any random emotional post.
- Keep it respectful, premium, emotional, and culturally specific.
"""


def build_event_image_instruction(event: Dict[str, Any]) -> str:
    """Create a short but explicit visual identity instruction for image scenes."""
    if not event:
        return ""

    event_name = str(event.get("name", "special occasion")).strip()
    visuals = _event_iconic_visuals(event)
    visual_text = ", ".join(visuals[:5]) if visuals else "iconic symbols tied to the occasion"

    return (
        f"EVENT IMAGE FOCUS: The scene must clearly read as {event_name}. "
        f"Prioritize iconic visual elements: {visual_text}. "
        "Do not use generic abstract nature or random rainy-city imagery unless it supports the occasion. "
        "The composition should clearly communicate what this event is famous for."
    )


def build_quote_event_instruction(event: Dict[str, Any]) -> str:
    """Build prompt text to steer quote generation for an active event."""
    hashtags = " ".join(event.get("hashtags", [])[:5])
    wish = get_event_wish(event)
    event_identity = build_event_identity_instruction(event)

    return f"""

==================================================
SPECIAL DATE CONTENT MODE

Today is related to: {event.get('name', 'a special occasion')}.
Region/Audience: {event.get('region', 'South Asian audience')}.
Language style: {event.get('language_style', 'simple emotional English')}.
Theme: {event.get('quote_theme', '')}.

Generate content that feels timely, emotional, respectful, and highly shareable for this occasion.
Keep the existing format and word-length rules from the selected content type, but make the emotion clearly connected to this occasion.
{event_identity}
Do not include wishes like "{wish}" in the generated quote text. Event wishes are handled only in the social caption.

Safety rules:
- Keep it inclusive and respectful.
- Make event content gender-neutral. Do not use he, she, him, her, boyfriend, girlfriend, husband, wife, or gendered relationship framing.
- If the selected base prompt asks for he/she relationship content, override that requirement and use neutral words like someone, people, we, us, they, the heart, a person, or a soul.
- Do not create event quotes like "she posts about freedom" or "he talks about independence"; keep the message universal.
- Avoid political party references.
- Avoid religious superiority or comparison.
- Avoid hate, controversy, or aggressive slogans.
- Do not copy copyrighted poems, songs, speeches, or famous quotes.
- Make it original and natural.

Helpful hashtags/context, do not include hashtags in the quote unless the original format asks for them:
{hashtags}
==================================================
"""


def build_reel_event_instruction(event: Dict[str, Any]) -> str:
    """Build prompt text to steer reel story generation for an active event."""
    visual_hints = event.get("visual_hints", []) or []
    visual_hint_text = "\n".join(f"- {hint}" for hint in visual_hints)
    hashtags = " ".join(event.get("hashtags", [])[:6])
    event_identity = build_event_identity_instruction(event)

    return f"""

==================================================
SPECIAL DATE REEL MODE

Today is related to: {event.get('name', 'a special occasion')}.
Region/Audience: {event.get('region', 'South Asian audience')}.
Language style: {event.get('language_style', 'simple emotional English')}.
Reel theme: {event.get('reel_theme', '')}.
Quote/emotional theme: {event.get('quote_theme', '')}.

Create the reel so people connected to this occasion can feel it, save it, and share it.
Use the selected normal content category as the base emotion, but make the story clearly relevant to this occasion.
{event_identity}

Visual hints to naturally include where suitable:
{visual_hint_text}

Safety rules:
- Keep it inclusive, respectful, and culturally warm.
- Make event narration gender-neutral unless a specific culturally necessary role is required. Prefer someone, people, we, us, they, families, friends, children, elders, citizens, or a person.
- Do not make event reels centered on he/she relationship drama. The occasion should feel universal and shareable.
- Avoid political party references.
- Avoid religious superiority or comparison.
- Avoid hate, controversy, violence, or aggressive slogans.
- Do not copy copyrighted poems, songs, speeches, or famous quotes.
- Keep it original, cinematic, emotional, and shareable.

Caption context/hashtags for later:
{hashtags}
==================================================
"""


def get_event_hashtags(event: Optional[Dict[str, Any]], max_count: int = 6) -> List[str]:
    if not event:
        return []

    hashtags = event.get("hashtags", []) or []
    return [tag for tag in hashtags if isinstance(tag, str) and tag.startswith("#")][:max_count]


def build_event_caption_prefix(event: Optional[Dict[str, Any]]) -> str:
    if not event:
        return ""

    name = event.get("name", "").strip()
    if not name:
        return ""

    if event.get("is_exact_date"):
        return f"{name} special"

    days_until = int(event.get("days_until", 0) or 0)
    if days_until > 0:
        return f"{name} is almost here"

    return f"{name} memories"


def build_quote_caption(event: Optional[Dict[str, Any]], base_caption: str = "") -> str:
    """Build quote-post caption with event wish and hashtags when available."""
    caption_parts = []
    clean_base = (base_caption or "").strip()
    wish = get_event_wish(event)
    event_hashtags = " ".join(get_event_hashtags(event))

    if clean_base:
        caption_parts.append(clean_base)

    if wish:
        caption_parts.append(wish)

    if event_hashtags:
        caption_parts.append(event_hashtags)

    return "\n\n".join(caption_parts)

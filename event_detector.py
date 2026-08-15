"""
event_detector.py

Date-aware content enhancement for Aesthetic Vibes.

This module adds an optional event layer on top of the existing random content
logic. The event lookup flow is:

    current date -> event_date_lookup.json (date -> event name)
                 -> content_calendar.json (event name -> event details)

Event resolution order:
1. Fixed (recurring MM-DD) events are resolved first; the best fixed event
   wins whenever one is active for the day.
2. Dated (year-specific YYYY-MM-DD) events are only considered when no fixed
   event is active that day.
3. If a fixed and a dated event overlap on the same day (e.g. Netaji Jayanti
   + Saraswati Puja on 2026-01-23, or World Music Day + Fathers' Day on
   2026-06-21), the day's content is distributed across both: each quote/reel
   run picks the next event from the fixed-then-dated rotation, so both
   occasions receive a few quotes and a few reels.

If no event matches, the existing random logic continues unchanged.
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

IST = timezone(timedelta(hours=5, minutes=30))
CALENDAR_FILE = Path(__file__).resolve().parent / "content_calendar.json"
DATE_NAME_LOOKUP_FILES = [
    Path(__file__).resolve().parent / "event_date_lookup_2026.json",
    Path(__file__).resolve().parent / "event_date_lookup.json",
]

PRIORITY_WEIGHT = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

# Event source/bucket tags attached to every active event.
SOURCE_FIXED = "fixed_events"   # recurring MM-DD dates
SOURCE_DATED = "dated_events"   # year-specific YYYY-MM-DD dates

# Content types (matched against smart_scheduler.ContentType.value) used to
# rotate overlapping fixed/dated events across the day.
CONTENT_QUOTE = "quote"
CONTENT_REEL = "reel"

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


def _load_date_name_lookup() -> Dict[str, str]:
    """Load the year-specific date-to-name mapping from a separate JSON file."""
    for candidate in DATE_NAME_LOOKUP_FILES:
        if not candidate.exists():
            continue
        try:
            with candidate.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except Exception as exc:
            print(f"⚠️ Could not read date-name lookup '{candidate.name}': {exc}")
            continue

        if isinstance(payload, dict):
            cleaned = {}
            for date_key, event_name in payload.items():
                if isinstance(date_key, str) and isinstance(event_name, str):
                    cleaned[date_key.strip()] = event_name.strip()
            return cleaned

    return {}


def _load_calendar_from_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Load events keyed by event name from content_calendar.json."""
    events: Dict[str, Dict[str, Any]] = {}

    # New structure: {"events": {event_name: details}}
    events_bucket = data.get("events", {}) or {}
    if isinstance(events_bucket, dict):
        for event_name, event_data in events_bucket.items():
            if not isinstance(event_data, dict):
                continue
            cleaned_name = str(event_data.get("name") or event_name).strip()
            cleaned_data = dict(event_data)
            cleaned_data["name"] = cleaned_name
            events[cleaned_name] = cleaned_data

    # Backward compatibility: legacy fixed_events/dated_events buckets.
    if not events:
        for bucket_name in ("fixed_events", "dated_events"):
            bucket = data.get(bucket_name, {}) or {}
            if not isinstance(bucket, dict):
                continue
            for event_name, event_data in bucket.items():
                if not isinstance(event_data, dict):
                    continue
                cleaned_name = str(event_data.get("name") or event_name).strip()
                cleaned_data = dict(event_data)
                cleaned_data["name"] = cleaned_name
                events[cleaned_name] = cleaned_data

    return {"events": events}


def _load_calendar() -> Dict[str, Any]:
    if not CALENDAR_FILE.exists():
        return {"events": {}}

    try:
        with CALENDAR_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as exc:
        print(f"⚠️ Could not read event calendar: {exc}")
        return {"events": {}}

    return _load_calendar_from_data(data)


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
    """Return all calendar events active for today in IST.

    Flow: current date -> event_date_lookup.json (date -> event name)
          -> content_calendar.json (event name -> event details).
    """
    today = get_effective_now(now)
    calendar = _load_calendar()
    events_by_name = calendar.get("events", {})
    date_name_lookup = _load_date_name_lookup()

    active_events: List[Dict[str, Any]] = []

    for date_key, event_name in date_name_lookup.items():
        event = events_by_name.get(str(event_name).strip())
        if not event:
            continue

        try:
            if len(date_key.split("-")) == 2:
                # Fixed date (MM-DD) that recurs every year.
                month, day = map(int, date_key.split("-"))
                event_date = today.replace(month=month, day=day)
                source = SOURCE_FIXED
            else:
                # Year-specific date (YYYY-MM-DD).
                event_date = datetime.strptime(date_key, "%Y-%m-%d").replace(tzinfo=IST)
                source = SOURCE_DATED
        except Exception:
            print(f"⚠️ Invalid event date key: {date_key}")
            continue

        if _event_matches(event_date, today, event):
            active_events.append(_with_runtime_fields(event, event_date, today, date_key, source))

    return sorted(
        active_events,
        key=lambda item: (
            # Fixed (recurring MM-DD) events always take precedence over
            # year-specific dated events, then sort by priority/exactness.
            1 if item.get("source") == SOURCE_FIXED else 0,
            PRIORITY_WEIGHT.get(str(item.get("priority", "low")).lower(), 1),
            1 if item.get("is_exact_date") else 0,
            -abs(int(item.get("days_until", 0))),
        ),
        reverse=True,
    )


def _content_run_index(content_type: Optional[str], now: Optional[datetime] = None) -> int:
    """Return the 0-based run offset of today for a given content type.

    Quotes post twice a day (morning/evening) and reels three times
    (afternoon/prime/late) in smart_scheduler.py's WEEKLY_SCHEDULE. Hours are
    IST. Used only when fixed and dated events overlap on the same day, so the
    day's slots alternate between the two occasions instead of always favouring
    one.
    """
    ist = get_effective_now(now).astimezone(IST)
    minutes = ist.hour * 60 + ist.minute

    if content_type == CONTENT_REEL:
        if minutes < 17 * 60:
            return 0  # afternoon_reel
        if minutes < 22 * 60:
            return 1  # prime_reel
        return 2      # late_reel
    if content_type == CONTENT_QUOTE:
        if minutes < 13 * 60:
            return 0  # morning_quote
        return 1      # evening_quote
    return 0


def get_today_event(
    now: Optional[datetime] = None,
    content_type: Optional[str] = None,
    run_index: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Return the event to theme the current content run around.

    Resolution order:
    1. Fixed (recurring MM-DD) events are checked first; the best fixed
       event wins whenever one is active for the day.
    2. Dated (year-specific YYYY-MM-DD) events are only considered when no
       fixed event is active.
    3. If a fixed and a dated event fall on the exact same day, the day's
       content is distributed between them: each quote/reel run picks the
       next event from the fixed-then-dated rotation, so both occasions
       gather a few quotes and a few reels. Lead/linger windows ("1 day
       before") are not counted as overlaps.

    Args:
        now: Optional datetime to evaluate against (IST-aware or naive).
        content_type: "quote" or "reel" — used to derive the day's run slot
            when fixed and dated events overlap. None keeps legacy behaviour
            (the fixed event wins).
        run_index: Explicit 0-based run of the day for ``content_type``;
            overrides the time-based derivation (mainly for testing).
    """
    events = get_active_events(now=now)
    if not events:
        return None

    fixed_events = [event for event in events if event.get("source") == SOURCE_FIXED]
    dated_events = [event for event in events if event.get("source") == SOURCE_DATED]

    if not fixed_events:
        # No recurring (MM-DD) event today — fall back to dated events.
        event = dated_events[0]
        print(f"🎉 Event mode active: {event.get('name')} ({event.get('date_key')}) [dated]")
        return event

    if not dated_events:
        # A fixed event is active and nothing overlaps it.
        event = fixed_events[0]
        print(f"🎉 Event mode active: {event.get('name')} ({event.get('date_key')}) [fixed]")
        return event

    # A real overlap only exists when BOTH occasions fall exactly on today's
    # date (lead/linger windows such as "1 day before" are not treated as an
    # overlap, they are just the surrounding pre/post window of the occasion).
    exact_fixed = [event for event in fixed_events if event.get("is_exact_date")]
    exact_dated = [event for event in dated_events if event.get("is_exact_date")]

    if exact_fixed and exact_dated and content_type:
        # Same-day overlap: rotate fixed -> dated -> fixed -> ... across the
        # day's slots so both occasions get a few quotes and a few reels.
        pool = exact_fixed + exact_dated
        idx = run_index if run_index is not None else _content_run_index(content_type, now)
        event = pool[idx % len(pool)]
        print(
            f"🎉 Event mode active: {event.get('name')} ({event.get('date_key')}) "
            f"[overlap: {content_type} slot #{idx}]"
        )
        return event

    if exact_dated and not exact_fixed:
        # The dated event is today's exact occasion; any active fixed event is
        # only in a lead/linger window around its own date.
        event = exact_dated[0]
        print(f"🎉 Event mode active: {event.get('name')} ({event.get('date_key')}) [dated exact]")
        return event

    # Fixed event is today's occasion (or active without an exact dated match).
    event = fixed_events[0]
    print(f"🎉 Event mode active: {event.get('name')} ({event.get('date_key')}) [fixed]")
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
    """Return prioritized event visual cues.

    Single source of truth is ``visual_hints`` inside each event entry in
    content_calendar.json — edit only that file to add/change keywords and
    items for an event's image prompts. No code-side maps.
    """
    cues = [str(v).strip() for v in (event.get("visual_hints") or []) if str(v).strip()]
    deduped = []
    seen = set()
    for cue in cues:
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
    """Build prompt text to steer reel story generation for an active event.

    Event days only. Makes Gemini write a nostalgic, first-person memory story
    about the occasion — explicitly overriding the generic "not a story / no
    events" base direction of the reel prompt.
    """
    visual_hints = event.get("visual_hints", []) or []
    visual_hint_text = "\n".join(f"- {hint}" for hint in visual_hints)
    hashtags = " ".join(event.get("hashtags", [])[:6])
    event_identity = build_event_identity_instruction(event)
    name = str(event.get("name", "a special occasion")).strip() or "a special occasion"

    return f"""

==================================================
SPECIAL DATE REEL MODE  (ABSOLUTE OVERRIDE — ONLY RUNS TODAY)
==================================================

Today is the occasion: {name}.
Region/Audience: {event.get('region', 'South Asian audience')}.
Language style: {event.get('language_style', 'simple emotional English')}.

Occasion story to follow (this is the heart of the narration):
{event.get('reel_theme', 'a nostalgic memory of this occasion')}

Emotional/quote themes to borrow nostalgia from:
{event.get('quote_theme', '')}

RULE 1 — WRITE THE OCCASION'S STORY, NOT A GENERIC POST
The narration MUST be an 80-110 word first-person nostalgic story clearly about {name}.
Earlier instructions saying "content is not a story", "no events", "no places",
"no characters", "no fictional situations" DO NOT APPLY today — ignore them.
The selected content category only supplies the mood/emotion; it is never the
subject. Do not list dates, facts, history, or "Happy {name}" greetings.

RULE 2 — NOSTALGIA BEFORE EVERYTHING
Make it feel like remembering, not reporting: childhood or earlier years, the
places and rituals the occasion always carried, sounds and smells it brought,
family and friends who were around then, people who are now farther away,
routines we stopped repeating but still miss.

NOSTALGIC STORY BEATS (use all four in order within the 80-110 words):
1. Open on ONE specific sensory memory connected to {name} — a sound, smell,
   light, food, object, or a small thing that only the occasion had.
2. Grow it into the feeling the occasion once gave: home, togetherness,
   innocence, or belonging.
3. Turn quietly toward today: time has passed, things changed, some people are
   no longer near.
4. End warm and shareable: even now, the occasion still lives inside these
   memories.

RULE 3 — SCENES ARE FRAMES OF THE MEMORY
Each of the 6 scenes must look like a frame from that memory (not a postcard
of the event): old familiar places, afternoon or monsoon/dawn light, common
objects, small gestures, quiet colour. Weave in these visuals where suitable:
{visual_hint_text}
{event_identity}

RULE 4 — VOICE
Keep the {event.get('language_style', 'simple emotional English')} tone.
Gender-neutral when people appear. Simple, warm, believable — no forced poetry.

Safety rules:
- Make event narration gender-neutral unless a specific culturally necessary role is required. Prefer someone, people, we, us, they, families, friends, children, elders, citizens, or a person.
- Do not make event reels centred on romance/he-she drama; the occasion should feel universal and shareable.
- Avoid political party references.
- Avoid religious superiority or comparison.
- Avoid hate, controversy, violence, or aggressive slogans.
- Do not copy copyrighted poems, songs, speeches, or famous quotes.
- Keep it original, cinematic, and nostalgic without being sad or hopeless.

Caption context/hashtags for later:
{hashtags}
===================================================
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

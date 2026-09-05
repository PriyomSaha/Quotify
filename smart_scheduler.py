"""
smart_scheduler.py - Robust Content Scheduling System for GitHub Actions

Handles both quotes and reels with:
- Weekly posting windows (time ranges, not exact times)
- Missed run recovery
- Duplicate prevention
- Reel generation time compensation (20-25 min)
- 90-120 min spacing between any content
- Synchronized state via GitHub Gist
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import requests
import os
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

# Import event detector for event-based daily limits
from event_detector import get_today_event, CONTENT_QUOTE, CONTENT_REEL

# ============================================================================
# CONFIGURATION
# ============================================================================

# GitHub Gist for shared state
# If SCHEDULER_GIST_ID is not set, scheduler state is stored as a separate
# file inside the existing CONTENT_HISTORY_GIST_ID gist.
SCHEDULER_GIST_ID = os.getenv("SCHEDULER_GIST_ID") or os.getenv("CONTENT_HISTORY_GIST_ID")
GITHUB_TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
GIST_FILENAME = "scheduler_state.json"

# Facebook API for checking recent posts
PAGE_ID = os.getenv("PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
API_VERSION = os.getenv("API_VERSION", "v21.0")

# Timing constraints
MIN_SPACING_MINUTES = 90  # Minimum time between any two posts
REEL_GENERATION_TIME = 25  # Minutes needed to generate a reel
WINDOW_GRACE_PERIOD = 15  # Minutes after window closes to still publish (tightened to avoid odd-hour drift)
QUOTE_LOOKAHEAD_MINUTES = 5  # Small buffer before a quote window starts, not a random publish time
MISSED_WINDOW_RECOVERY_MINUTES = 45  # Allow a late quote recovery after a recent missed window (tightened; 45 min keeps recovery within the same quarter-day block)
ACTIVE_JOB_TIMEOUT_MINUTES = 60  # Clear stale generation locks after this time
# Hard backstop against odd-hour publishing (prevents posts landing at 1 AM IST, etc.)
MIN_PUBLISH_HOUR = 6   # Earliest publish/generation start (06:00 IST)
MAX_PUBLISH_HOUR = 21  # A publish/reel-generation must complete by 21:00 IST — last slot is 20:00 reel


class ContentType(Enum):
    QUOTE = "quote"
    REEL = "reel"


# ============================================================================
# EVENT-BASED DAILY LIMITS
# ============================================================================

# Standard daily limits (no event)
DEFAULT_QUOTE_LIMIT = 2
DEFAULT_REEL_LIMIT = 2

# Event-based daily limits (when an event is active)
EVENT_QUOTE_LIMIT = 1
EVENT_REEL_LIMIT = 1


def _get_event_daily_limit(content_type: ContentType) -> int:
    """
    Return the daily publishing limit based on whether an event is active.

    When an event is detected for today, publishing is limited to:
    - 1 quote per day
    - 1 reel per day

    When no event is active, the default limits apply:
    - 2 quotes per day
    - 2 reels per day
    """
    if content_type == ContentType.QUOTE:
        event = get_today_event(content_type=CONTENT_QUOTE)
        if event:
            print(f"🎪 Event active: {event.get('name')} - Quote limit is {EVENT_QUOTE_LIMIT}/day")
            return EVENT_QUOTE_LIMIT
        return DEFAULT_QUOTE_LIMIT

    if content_type == ContentType.REEL:
        event = get_today_event(content_type=CONTENT_REEL)
        if event:
            print(f"🎪 Event active: {event.get('name')} - Reel limit is {EVENT_REEL_LIMIT}/day")
            return EVENT_REEL_LIMIT
        return DEFAULT_REEL_LIMIT

    return DEFAULT_QUOTE_LIMIT


@dataclass
class PostingWindow:
    """Represents a time window for posting content"""
    name: str
    content_type: ContentType
    start_hour: int  # IST hour (0-23)
    start_minute: int
    end_hour: int  # IST hour (0-23)
    end_minute: int
    priority: int  # Higher = more important (for engagement)

    def to_minutes(self, hour: int, minute: int) -> int:
        """Convert hour:minute to minutes since midnight"""
        return hour * 60 + minute
    
    def start_minutes(self) -> int:
        return self.to_minutes(self.start_hour, self.start_minute)
    
    def end_minutes(self) -> int:
        return self.to_minutes(self.end_hour, self.end_minute)
    
    def is_current(self, ist_now: datetime) -> bool:
        """Check if current time is within this window"""
        current_minutes = self.to_minutes(ist_now.hour, ist_now.minute)
        return self.start_minutes() <= current_minutes <= self.end_minutes()
    
    def is_recently_passed(self, ist_now: datetime) -> bool:
        """Check if window just closed (within grace period)"""
        current_minutes = self.to_minutes(ist_now.hour, ist_now.minute)
        window_end = self.end_minutes()
        return window_end < current_minutes <= (window_end + WINDOW_GRACE_PERIOD)

    def is_recently_missed(self, ist_now: datetime) -> bool:
        """Check if a quote window was missed recently and still qualifies for late recovery"""
        current_minutes = self.to_minutes(ist_now.hour, ist_now.minute)
        window_end = self.end_minutes()
        return window_end < current_minutes <= (window_end + MISSED_WINDOW_RECOVERY_MINUTES)

    def starts_within(self, ist_now: datetime, lookahead_minutes: int) -> bool:
        """Check whether this window starts within the next lookahead_minutes"""
        current_minutes = self.to_minutes(ist_now.hour, ist_now.minute)
        return 0 <= (self.start_minutes() - current_minutes) <= lookahead_minutes
    
    def should_start_generation(self, ist_now: datetime) -> bool:
        """
        For reels: Check if we should start generation now
        (to finish within the window)
        """
        if self.content_type != ContentType.REEL:
            return self.is_current(ist_now)
        
        # For reels, start generation REEL_GENERATION_TIME minutes before window start
        current_minutes = self.to_minutes(ist_now.hour, ist_now.minute)
        generation_start = self.start_minutes() - REEL_GENERATION_TIME
        
        # Check if we're in the generation window or posting window
        return generation_start <= current_minutes <= self.end_minutes()


# ============================================================================
# WEEKLY SCHEDULE - IST TIMEZONE
# ============================================================================

# ---------------------------------------------------------------------------
# Ideal Daily 4-Post Schedule (IST)
#   8:00 AM  – Quote 1   (morning energy)
#  12:00 PM  – Reel 1    (lunch-break video)
#   4:00 PM  – Quote 2   (late-afternoon / end-of-work commute)
#   8:00 PM  – Reel 2    (peak evening unwind window)
#
# The `late_reel` slot that previously published at 22:15–23:45 IST has been
# REMOVED entirely so no content is ever scheduled in odd/late hours.
# Reel generation windows start REEL_GENERATION_TIME (25 min) before the
# published time so the finished video lands inside the window below.
# ---------------------------------------------------------------------------
WEEKLY_SCHEDULE: Dict[str, List[PostingWindow]] = {
    "monday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 8, 50, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 12, 0, 12, 50, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 16, 0, 16, 50, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 20, 50, priority=5),
    ],
    "tuesday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 8, 50, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 12, 0, 12, 50, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 16, 0, 16, 50, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 20, 50, priority=5),
    ],
    "wednesday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 8, 50, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 12, 0, 12, 50, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 16, 0, 16, 50, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 20, 50, priority=5),
    ],
    "thursday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 8, 50, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 12, 0, 12, 50, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 16, 0, 16, 50, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 20, 50, priority=5),
    ],
    "friday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 8, 50, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 12, 0, 12, 50, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 16, 0, 16, 50, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 20, 50, priority=5),
    ],
    "saturday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 8, 50, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 12, 0, 12, 50, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 16, 0, 16, 50, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 20, 50, priority=5),
    ],
    "sunday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 8, 50, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 12, 0, 12, 50, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 16, 0, 16, 50, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 20, 50, priority=5),
    ],
}


# ============================================================================
# STATE MANAGEMENT (GitHub Gist)
# ============================================================================

@dataclass
class SchedulerState:
    """Shared state synchronized via GitHub Gist"""
    date: str  # YYYY-MM-DD in IST
    completed_slots: List[str]  # List of window names completed today
    last_post_time: Optional[str]  # ISO timestamp of last post (any type)
    last_quote_time: Optional[str]  # ISO timestamp of last quote
    last_reel_time: Optional[str]  # ISO timestamp of last reel
    daily_quote_count: int
    daily_reel_count: int
    active_job: Optional[Dict[str, str]] = None  # currently running quote/reel job lock
    # --- Date pause (toggled via the "Pause Manager" workflow; skip ALL posts that day) ---
    paused_dates: List[str] = field(default_factory=list)  # one-off "YYYY-MM-DD" paused days
    # --- Event content tracking (ensures unique content across event days) ---
    event_content_tracker: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def _today_key() -> str:
    """Return today's date in IST, because posting windows are IST based."""
    ist_offset = timedelta(hours=5, minutes=30)
    return (datetime.now(timezone.utc) + ist_offset).strftime("%Y-%m-%d")


def _default_scheduler_state(previous: Optional[Dict[str, Any]] = None) -> SchedulerState:
    """Create a safe default scheduler state without recursive calls."""
    previous = previous or {}
    return SchedulerState(
        date=_today_key(),
        completed_slots=[],
        last_post_time=previous.get("last_post_time"),
        last_quote_time=previous.get("last_quote_time"),
        last_reel_time=previous.get("last_reel_time"),
        daily_quote_count=0,
        daily_reel_count=0,
        active_job=None,
        paused_dates=[],
        event_content_tracker=previous.get("event_content_tracker", {}),
    )


def _state_from_dict(state_dict: Dict[str, Any]) -> SchedulerState:
    """Load state with backward-compatible defaults for newly added fields."""
    state_dict = dict(state_dict)
    today = _today_key()

    if state_dict.get("date") != today:
        print(f"📅 State is from {state_dict.get('date')}, resetting for today ({today})")
        return _default_scheduler_state(state_dict)

    return SchedulerState(
        date=state_dict.get("date", today),
        completed_slots=state_dict.get("completed_slots", []),
        last_post_time=state_dict.get("last_post_time"),
        last_quote_time=state_dict.get("last_quote_time"),
        last_reel_time=state_dict.get("last_reel_time"),
        daily_quote_count=state_dict.get("daily_quote_count", 0),
        daily_reel_count=state_dict.get("daily_reel_count", 0),
        active_job=state_dict.get("active_job"),
        paused_dates=list(state_dict.get("paused_dates", []) or []),
        event_content_tracker=state_dict.get("event_content_tracker", {}),
    )


def get_scheduler_state() -> SchedulerState:
    """Load scheduler state from GitHub Gist."""
    if not SCHEDULER_GIST_ID or not GITHUB_TOKEN:
        print("⚠️ Scheduler gist/token not set - using in-memory default state")
        return _default_scheduler_state()
    
    try:
        print("🔄 Loading scheduler state from GitHub Gist...")
        url = f"https://api.github.com/gists/{SCHEDULER_GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            gist_data = response.json()
            
            if GIST_FILENAME in gist_data.get("files", {}):
                content = gist_data["files"][GIST_FILENAME]["content"]
                state = _state_from_dict(json.loads(content))
                print(f"✅ State loaded: {len(state.completed_slots)} slots completed")
                return state

            print("⚠️ Scheduler state file not found in gist - creating it now")
            default_state = _default_scheduler_state()
            save_scheduler_state(default_state)
            return default_state
                
        print(f"⚠️ Failed to fetch gist: {response.status_code} - using default state")
        return _default_scheduler_state()
            
    except Exception as e:
        print(f"⚠️ Error loading state: {e} - using default state")
        return _default_scheduler_state()


def save_scheduler_state(state: SchedulerState) -> bool:
    """Save scheduler state to GitHub Gist"""
    if not SCHEDULER_GIST_ID or not GITHUB_TOKEN:
        print("⚠️ SCHEDULER_GIST_ID or GITHUB_TOKEN not set - cannot save state")
        return False
    
    try:
        print(f"📤 Saving scheduler state to GitHub Gist...")
        url = f"https://api.github.com/gists/{SCHEDULER_GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps(asdict(state), indent=2)
                }
            }
        }
        
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ State saved to gist")
            return True
        else:
            print(f"⚠️ Failed to save gist: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️ Error saving state: {e}")
        return False


def _active_job_is_stale(active_job: Optional[Dict[str, str]]) -> bool:
    """Return True when an active job lock is old enough to ignore."""
    if not active_job or not active_job.get("started_at"):
        return True

    try:
        started_at = datetime.fromisoformat(active_job["started_at"])
        age_minutes = int((datetime.now(timezone.utc) - started_at).total_seconds() / 60)
        return age_minutes >= ACTIVE_JOB_TIMEOUT_MINUTES
    except Exception:
        return True


def _active_job_blocks(state: SchedulerState) -> Tuple[bool, str]:
    """Check whether another workflow is currently generating/uploading content."""
    if not state.active_job:
        return False, "No active job"

    if _active_job_is_stale(state.active_job):
        print(f"⚠️ Found stale active job lock, ignoring: {state.active_job}")
        state.active_job = None
        save_scheduler_state(state)
        return False, "Stale active job cleared"

    job_type = state.active_job.get("type", "unknown")
    slot = state.active_job.get("slot", "unknown")
    started_at = state.active_job.get("started_at", "unknown")
    return True, f"Another job is running: {job_type}/{slot} started at {started_at}"


def acquire_run_lock(content_type: ContentType, window: Optional[PostingWindow] = None) -> bool:
    """Reserve the current slot before generation starts."""
    window = window or get_active_window(content_type)
    if not window:
        print("❌ Cannot acquire lock because there is no active window")
        return False

    state = get_scheduler_state()

    if window.name in state.completed_slots:
        print(f"❌ Cannot acquire lock: slot '{window.name}' already completed")
        return False

    blocked, reason = _active_job_blocks(state)
    if blocked:
        print(f"❌ Cannot acquire lock: {reason}")
        return False

    state.active_job = {
        "type": content_type.value,
        "slot": window.name,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    saved = save_scheduler_state(state)
    if saved:
        print(f"🔒 Active job lock acquired: {content_type.value}/{window.name}")
    return saved


def release_run_lock(content_type: Optional[ContentType] = None, window: Optional[PostingWindow] = None, force: bool = False) -> bool:
    """Clear the active job lock after success or failure."""
    state = get_scheduler_state()
    if not state.active_job:
        print("🔓 No active job lock to release")
        return True

    if not force and content_type and window:
        if state.active_job.get("type") != content_type.value or state.active_job.get("slot") != window.name:
            print(f"⚠️ Active lock belongs to another job, not releasing: {state.active_job}")
            return False

    print(f"🔓 Releasing active job lock: {state.active_job}")
    state.active_job = None
    return save_scheduler_state(state)


def mark_slot_completed(window: PostingWindow) -> None:
    """Mark a posting window as completed after confirmed upload success."""
    state = get_scheduler_state()
    now = datetime.now(timezone.utc).isoformat()
    already_completed = window.name in state.completed_slots
    
    if not already_completed:
        state.completed_slots.append(window.name)
    
    state.last_post_time = now
    
    if window.content_type == ContentType.QUOTE:
        state.last_quote_time = now
        if not already_completed:
            state.daily_quote_count += 1
    else:
        state.last_reel_time = now
        if not already_completed:
            state.daily_reel_count += 1

    state.active_job = None
    save_scheduler_state(state)


# ============================================================================
# EVENT CONTENT TRACKING - Ensures unique content across event days
# ============================================================================

def _get_event_tracker(state: SchedulerState, event_name: str) -> Dict[str, Any]:
    """Get or initialize the tracker for a specific event."""
    if event_name not in state.event_content_tracker:
        state.event_content_tracker[event_name] = {
            "active_window": None,
            "used_angles": [],
            "used_moods": [],
            "used_triggers": [],
            "daily_posts": {},
        }
    return state.event_content_tracker[event_name]


def _split_theme_to_angles(theme_string: str) -> List[str]:
    """Split a theme string into unique content angles."""
    if not theme_string:
        return []
    angles = [angle.strip() for angle in theme_string.split(",") if angle.strip()]
    return angles


def _get_unique_angle(state: SchedulerState, event: Dict[str, Any], content_type: str) -> str:
    """Get a unique content angle for today's event content."""
    event_name = event.get("name", "unknown")
    tracker = _get_event_tracker(state, event_name)

    if content_type == "quote":
        all_angles = _split_theme_to_angles(event.get("quote_theme", ""))
    else:
        all_angles = _split_theme_to_angles(event.get("reel_theme", ""))
        memory_triggers = event.get("memory_triggers", [])
        if memory_triggers:
            all_angles.extend([f"memory of {t}" for t in memory_triggers[:3]])

    used_angles = tracker.get("used_angles", [])
    unused_angles = [a for a in all_angles if a not in used_angles]

    if unused_angles:
        return unused_angles[0]
    else:
        return "different perspective"


def _get_unique_mood(state: SchedulerState, event: Dict[str, Any]) -> str:
    """Get a unique emotional mood for today's event content."""
    event_name = event.get("name", "unknown")
    tracker = _get_event_tracker(state, event_name)

    all_moods = event.get("emotional_mood", [])
    used_moods = tracker.get("used_moods", [])

    for mood in all_moods:
        if mood not in used_moods:
            return mood

    return all_moods[0] if all_moods else "nostalgic"


def _get_unique_trigger(state: SchedulerState, event: Dict[str, Any]) -> str:
    """Get a unique memory trigger for today's event content."""
    event_name = event.get("name", "unknown")
    tracker = _get_event_tracker(state, event_name)

    all_triggers = event.get("memory_triggers", [])
    used_triggers = tracker.get("used_triggers", [])

    for trigger in all_triggers:
        if trigger not in used_triggers:
            return trigger

    return all_triggers[0] if all_triggers else ""


def _initialize_event_window(state: SchedulerState, event: Dict[str, Any], event_name: str) -> None:
    """Initialize the event window when event first becomes active."""
    tracker = _get_event_tracker(state, event_name)

    if tracker.get("active_window") is None:
        active_before = int(event.get("active_before_days", 0) or 0)
        active_after = int(event.get("active_after_days", 0) or 0)

        ist_offset = timedelta(hours=5, minutes=30)
        today = (datetime.now(timezone.utc) + ist_offset).date()

        start_date = today - timedelta(days=active_before)
        end_date = today + timedelta(days=active_after)

        tracker["active_window"] = {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        }

        print(f"🎪 Event window initialized for {event_name}: {start_date} to {end_date}")


def _track_event_post(state: SchedulerState, event_name: str, event: Dict[str, Any], content_type: str) -> None:
    """Track that an event post was generated."""
    tracker = _get_event_tracker(state, event_name)
    today = _today_key()

    if today not in tracker.get("daily_posts", {}):
        tracker.setdefault("daily_posts", {})[today] = {"event_reel": False, "event_quote": False}

    if content_type == "quote":
        tracker["daily_posts"][today]["event_quote"] = True
    else:
        tracker["daily_posts"][today]["event_reel"] = True

    angle = _get_unique_angle(state, event, content_type)
    mood = _get_unique_mood(state, event)
    trigger = _get_unique_trigger(state, event)

    if angle not in tracker.get("used_angles", []):
        tracker.setdefault("used_angles", []).append(angle)
    if mood not in tracker.get("used_moods", []):
        tracker.setdefault("used_moods", []).append(mood)
    if trigger not in tracker.get("used_triggers", []):
        tracker.setdefault("used_triggers", []).append(trigger)

    print(f"📝 Tracked {content_type} for {event_name}: angle='{angle}', mood='{mood}'")


def _get_event_content_prompt_addition(state: SchedulerState, event: Dict[str, Any], content_type: str) -> str:
    """Generate additional prompt text to ensure unique content."""
    event_name = event.get("name", "unknown")
    tracker = _get_event_tracker(state, event_name)

    angle = _get_unique_angle(state, event, content_type)
    mood = _get_unique_mood(state, event)
    trigger = _get_unique_trigger(state, event)

    used_angles = tracker.get("used_angles", [])
    used_moods = tracker.get("used_moods", [])

    addition = "\n\nUNIQUENESS DIRECTIVE (IMPORTANT):\n"
    addition += f"- TODAY'S FOCUS: {angle}\n"
    addition += f"- TODAY'S MOOD: {mood}\n"
    if trigger:
        addition += f"- TODAY'S SENSORY ANCHOR: {trigger}\n"

    if used_angles and len(used_angles) > 1:
        addition += f"- AVOID THESE USED ANGLES: {', '.join(used_angles[:-1])}\n"
    if used_moods and len(used_moods) > 1:
        addition += f"- AVOID THESE USED MOODS: {', '.join(used_moods[:-1])}\n"

    addition += "- Make this content DISTINCT from previous posts. Different story, different angle, different feeling.\n"

    return addition


def _has_event_quota_available(state: SchedulerState, event_name: str) -> bool:
    """Check if the event has quota for more posts today."""
    tracker = _get_event_tracker(state, event_name)
    today = _today_key()

    daily_posts = tracker.get("daily_posts", {}).get(today, {"event_reel": False, "event_quote": False})

    if daily_posts.get("event_reel") and daily_posts.get("event_quote"):
        return False
    return True


def _get_event_post_type_available(state: SchedulerState, event_name: str, content_type: str) -> bool:
    """Check if the specific event post type is available today."""
    tracker = _get_event_tracker(state, event_name)
    today = _today_key()

    daily_posts = tracker.get("daily_posts", {}).get(today, {"event_reel": False, "event_quote": False})

    if content_type == "quote":
        return not daily_posts.get("event_quote", False)
    else:
        return not daily_posts.get("event_reel", False)


def _is_event_window_active(state: SchedulerState, event_name: str) -> bool:
    """Check if today is within the event's active window."""
    tracker = _get_event_tracker(state, event_name)
    active_window = tracker.get("active_window")

    if not active_window:
        return True

    today = _today_key()
    start = active_window.get("start", "")
    end = active_window.get("end", "")

    return start <= today <= end


def get_last_facebook_post_time() -> Optional[datetime]:
    """Get timestamp of most recent Facebook post"""
    if not PAGE_ID or not PAGE_ACCESS_TOKEN:
        print("⚠️ Facebook credentials not set")
        return None
    
    try:
        url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/posts"
        params = {
            "access_token": PAGE_ACCESS_TOKEN,
            "fields": "created_time",
            "limit": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            posts = data.get("data", [])
            
            if posts:
                created_time_str = posts[0]["created_time"]
                # Parse ISO format: 2026-08-05T10:30:00+0000
                last_post_time = datetime.fromisoformat(created_time_str.replace("+0000", "+00:00"))
                print(f"📊 Last Facebook post: {last_post_time.isoformat()}")
                return last_post_time
            else:
                print("📊 No recent Facebook posts found")
                return None
        else:
            print(f"⚠️ Facebook API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ Error fetching Facebook posts: {e}")
        return None


def minutes_since_last_post() -> Optional[int]:
    """Calculate minutes since last post (from state or Facebook)"""
    state = get_scheduler_state()
    
    # Check state first
    if state.last_post_time:
        last_time = datetime.fromisoformat(state.last_post_time)
        now = datetime.now(timezone.utc)
        minutes = int((now - last_time).total_seconds() / 60)
        print(f"⏱️ Minutes since last post (from state): {minutes}")
        return minutes
    
    # Fallback to Facebook API
    last_fb_post = get_last_facebook_post_time()
    if last_fb_post:
        now = datetime.now(timezone.utc)
        minutes = int((now - last_fb_post).total_seconds() / 60)
        print(f"⏱️ Minutes since last post (from Facebook): {minutes}")
        return minutes
    
    print("⏱️ No previous posts found - OK to post")
    return None


# ============================================================================
# SCHEDULING LOGIC
# ============================================================================

def get_ist_now() -> datetime:
    """Get current time in IST timezone"""
    utc_now = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    return utc_now + ist_offset


def get_current_weekday() -> str:
    """Get current weekday name in lowercase"""
    ist_now = get_ist_now()
    return ist_now.strftime("%A").lower()


def is_manual_dispatch_trigger() -> bool:
    """Return True when the workflow was started manually from GitHub Actions."""
    return os.getenv("GITHUB_EVENT_NAME", "").strip().lower() == "workflow_dispatch"


def get_current_windows(content_type: ContentType) -> List[PostingWindow]:
    """Get all windows for today that match the content type"""
    weekday = get_current_weekday()
    all_windows = WEEKLY_SCHEDULE.get(weekday, [])
    return [w for w in all_windows if w.content_type == content_type]


def get_pending_windows(content_type: ContentType, state: Optional[SchedulerState] = None) -> List[PostingWindow]:
    """Get pending windows for today that have not yet been completed."""
    state = state or get_scheduler_state()
    return [w for w in get_current_windows(content_type) if w.name not in state.completed_slots]


def get_next_pending_window(content_type: ContentType, state: Optional[SchedulerState] = None) -> Optional[PostingWindow]:
    """Return the next pending window for today, if any."""
    pending = get_pending_windows(content_type, state)
    return pending[0] if pending else None


def is_within_safe_publishing_hours(content_type: ContentType, ist_now: datetime) -> bool:
    """
    Hard backstop: never begin a publish (or reel generation) outside safe IST
    hours. For reels we reserve REEL_GENERATION_TIME so the *completion* never
    lands past MAX_PUBLISH_HOUR (e.g. a reel starting at 23:40 finishes ~00:05).
    Manual workflow_dispatch runs bypass should_publish_* entirely, so the
    backstop only governs scheduled (cron) runs.
    """
    current_minutes = ist_now.hour * 60 + ist_now.minute
    start_minutes = MIN_PUBLISH_HOUR * 60
    end_minutes = MAX_PUBLISH_HOUR * 60
    generation_buffer = REEL_GENERATION_TIME if content_type == ContentType.REEL else 0
    if current_minutes < start_minutes:
        return False
    if current_minutes + generation_buffer > end_minutes:
        return False
    return True


# ============================================================================
# DATE PAUSE - skip ALL posts on one chosen day
# ============================================================================

def _paused_reason(state: Optional[SchedulerState] = None) -> Tuple[bool, str]:
    """
    Return (is_paused, reason). Publishing is skipped when today (in IST) is a
    toggled pause date. There is no recurring/weekly concept - each day is set
    individually via the Pause Manager (defaults to today when no date is given).
    """
    state = state or get_scheduler_state()
    today = _today_key()  # "YYYY-MM-DD" in IST
    if today in state.paused_dates:
        return True, f"Today ({today}) is set as a paused day - all posts skipped"
    return False, ""


def get_pause_config() -> Dict[str, Any]:
    """Return the current pause settings and whether today is paused."""
    state = get_scheduler_state()
    today = _today_key()
    return {
        "paused_dates": sorted(state.paused_dates),
        "today": today,
        "paused_today": today in state.paused_dates,
    }


def set_pause_day(date_str: str = "", enabled: bool = True) -> Tuple[bool, str]:
    """
    Pause (enabled=True) or resume (enabled=False) ALL posts for ONE day.
    date_str is 'YYYY-MM-DD'; when empty it defaults to today (IST).
    """
    date_str = (date_str or "").strip()
    if not date_str:
        date_str = _today_key()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False, f"Invalid date '{date_str}'. Use YYYY-MM-DD, e.g. {_today_key()}"

    state = get_scheduler_state()
    paused = set(state.paused_dates)
    if enabled:
        paused.add(date_str)
        action = f"✅ {date_str} is now a PAUSED day - all posts skipped that day"
    else:
        paused.discard(date_str)
        action = f"✅ {date_str} is now active - normal publishing flow resumed"

    state.paused_dates = sorted(paused)
    if not save_scheduler_state(state):
        return False, "📤 Could not persist state to gist (check SCHEDULER_GIST_ID / GH_TOKEN)"
    return True, action


def _today_all_windows_sorted(ist_now: datetime) -> List[PostingWindow]:
    """All of today's windows (quotes + reels) sorted by start time."""
    weekday = ist_now.strftime('%A').lower()
    return sorted(WEEKLY_SCHEDULE.get(weekday, []), key=lambda w: w.start_minutes())


def _has_earlier_missed_post(ist_now: datetime, state: SchedulerState, active_window: PostingWindow) -> bool:
    """
    True if any scheduled slot that should have run BEFORE `active_window` has
    already started its window but was never completed today (i.e. it was
    missed/delayed). `active_window` itself is excluded so the slot currently
    being evaluated is never mistaken for an "earlier missed" post.
    """
    current_minutes = ist_now.hour * 60 + ist_now.minute
    for w in _today_all_windows_sorted(ist_now):
        if w.name == active_window.name:
            break
        if w.start_minutes() <= current_minutes and w.name not in state.completed_slots:
            return True
    return False


def _is_final_pending_window(window: PostingWindow, ist_now: datetime, state: SchedulerState) -> bool:
    """
    True if `window` is the last still-pending window of the day overall.
    The smart-skip rule suppresses this final slot when a prior slot was missed,
    so a delay never cascades into an odd-hour final post.
    """
    pending = [w for w in _today_all_windows_sorted(ist_now) if w.name not in state.completed_slots]
    return bool(pending) and pending[-1].name == window.name


def get_active_window(content_type: ContentType) -> Optional[PostingWindow]:
    """
    Get the currently active window for this content type.
    Returns None if no window is active or approaching.
    """
    if is_manual_dispatch_trigger():
        print("\n⚡ Manual workflow_dispatch trigger: detecting current IST time-frame...")
        ist_now = get_ist_now()

        # 1) See which time-frame the current IST time falls under (real-time detection).
        #    Publishing is unconditional on manual trigger — this only picks the slot/theme.
        windows = get_current_windows(content_type)
        for window in windows:
            if window.should_start_generation(ist_now):
                print(f"⚡ Manual dispatch: current time-frame detected — '{window.name}' ({content_type.value})")
                return window
            if window.is_current(ist_now):
                print(f"⚡ Manual dispatch: current time-frame detected — '{window.name}' ({content_type.value})")
                return window
            if window.is_recently_passed(ist_now):
                print(f"⚡ Manual dispatch: current time-frame (just closed, grace) — '{window.name}'")
                return window
            if content_type == ContentType.QUOTE and window.is_recently_missed(ist_now):
                print(f"⚡ Manual dispatch: current time-frame (missed-recovery) — '{window.name}'")
                return window
            if content_type == ContentType.QUOTE and window.starts_within(ist_now, QUOTE_LOOKAHEAD_MINUTES):
                minutes_until = window.start_minutes() - window.to_minutes(ist_now.hour, ist_now.minute)
                print(f"⚡ Manual dispatch: current time-frame (starts in {minutes_until} min) — '{window.name}'")
                return window

        # 2) No window is currently active — fall back to the next pending slot so
        #    the run still has a slot to record. There is NO publish/skip gate for
        #    manual runs: it always creates and publishes, regardless of window state.
        pending = get_pending_windows(content_type)
        if pending:
            print(f"⚡ Manual dispatch: no active time-frame right now; falling back to next-pending {content_type.value} slot '{pending[0].name}'")
            return pending[0]
        windows = get_current_windows(content_type)
        if windows:
            print(f"⚡ Manual dispatch: no active time-frame; falling back to first {content_type.value} slot '{windows[0].name}'")
            return windows[0]
        print("⚡ Manual dispatch: no windows scheduled for today; proceeding without a scheduler slot.")
        return None

    ist_now = get_ist_now()
    windows = get_current_windows(content_type)
    
    for window in windows:
        # For reels, check if we should start generation
        if window.should_start_generation(ist_now):
            return window
        
        # For quotes or if reel window is active
        if window.is_current(ist_now):
            return window
        
        # Check grace period for missed runs
        if window.is_recently_passed(ist_now):
            print(f"⏰ Window '{window.name}' just closed, within grace period")
            return window

        # For quotes, if a window was missed recently and no post has happened in 90 minutes,
        # allow late recovery for the missed window.
        if content_type == ContentType.QUOTE and window.is_recently_missed(ist_now):
            print(f"⏳ Quote window '{window.name}' was missed recently and may qualify for recovery")
            return window

        # For quotes, if a window starts very soon, allow early execution.
        # This is a narrow buffer only to avoid misses, not a free-form posting time.
        if content_type == ContentType.QUOTE and window.starts_within(ist_now, QUOTE_LOOKAHEAD_MINUTES):
            minutes_until = window.start_minutes() - window.to_minutes(ist_now.hour, ist_now.minute)
            print(f"⏳ Quote window '{window.name}' starts in {minutes_until} minutes, selecting it as a near-window preparation buffer")
            return window
    
    return None


def should_publish_quote(force_publish: bool = False) -> Tuple[bool, str]:
    """
    Determine if a quote should be published now
    Returns: (should_publish, reason)
    """
    # Off-day / pause toggle check. A paused day blocks quotes unless an
    # explicit force_publish is requested. This is checked before the manual
    # dispatch override so a toggled off-day also guards manual scheduler runs.
    if not force_publish:
        paused, pause_reason = _paused_reason()
        if paused:
            print("⏸️ QUOTE publishing is paused today:")
            print(f"   ↳ {pause_reason}")
            return False, f"Paused: {pause_reason}"

    if is_manual_dispatch_trigger():
        print("\n" + "="*70)
        print("⚡ MANUAL DISPATCH OVERRIDE - QUOTE")
        print("="*70)
        print("Manual workflow_dispatch trigger detected: bypassing all schedule/spacing/day-limit checks")
        return True, "Manual workflow_dispatch trigger: bypassing scheduling checks"

    print("\n" + "="*70)
    print("🤔 QUOTE SCHEDULER - Decision Process")
    print("="*70)
    
    ist_now = get_ist_now()
    print(f"📅 Current time (IST): {ist_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📆 Weekday: {get_current_weekday().title()}")
    
    # Step 1: Determine which quote window to use
    state = get_scheduler_state()
    if force_publish:
        active_window = get_next_pending_window(ContentType.QUOTE, state)
        if active_window:
            print(f"⚡ Manual force publish selected pending quote window: {active_window.name}")
        else:
            print("❌ No pending quote windows available for manual publish")
            return False, "No pending quote windows available"
    else:
        active_window = get_active_window(ContentType.QUOTE)
        if not active_window:
            print("❌ Not in a quote posting window")
            return False, "Not in a quote posting window"

    print(f"✅ Selected window: {active_window.name} ({active_window.start_hour}:{active_window.start_minute:02d} - {active_window.end_hour}:{active_window.end_minute:02d})")
    
    # Smart scheduling backstops - never post at odd hours, and if an earlier
    # slot today was missed, suppress the final slot so a delay never cascades
    # into an off-hours post.
    if not is_within_safe_publishing_hours(ContentType.QUOTE, ist_now):
        print('❌ Outside safe publishing hours (06:00-21:00 IST); skipping to avoid an odd-hour post.')
        return False, f'Outside safe publishing hours (IST {ist_now.hour:02d}:{ist_now.minute:02d})'
    if (not force_publish
            and _has_earlier_missed_post(ist_now, state, active_window)
            and _is_final_pending_window(active_window, ist_now, state)):
        print(f'❌ An earlier post was missed today; suppressing final slot {active_window.name!r}.')
        return False, 'Earlier post missed today; final-slot suppressed (smart-skip rule)'
    
    # Step 2: Check if this slot is already completed
    
    if active_window.name in state.completed_slots:
        print(f"❌ Slot '{active_window.name}' already completed today")
        return False, f"Slot '{active_window.name}' already completed today"

    blocked, lock_reason = _active_job_blocks(state)
    if blocked:
        print(f"❌ {lock_reason}")
        return False, lock_reason
    
    print(f"✅ Slot '{active_window.name}' not yet completed")
    
    # Step 3: Check minimum spacing
    minutes_since = minutes_since_last_post()
    
    if minutes_since is not None and minutes_since < MIN_SPACING_MINUTES:
        remaining = MIN_SPACING_MINUTES - minutes_since
        print(f"❌ Too soon after last post ({minutes_since} min ago, need {MIN_SPACING_MINUTES} min)")
        return False, f"Need {remaining} more minutes before next post"
    
    if minutes_since is not None:
        print(f"✅ Sufficient spacing: {minutes_since} minutes since last post")
    else:
        print(f"✅ No recent posts found - OK to post")

    # Step 4: Check daily limits (event-aware)
    daily_limit = _get_event_daily_limit(ContentType.QUOTE)
    if state.daily_quote_count >= daily_limit:
        print(f"❌ Daily quote limit reached ({state.daily_quote_count}/{daily_limit})")
        return False, f"Daily quote limit ({daily_limit}) reached"

    print(f"✅ Daily quote count: {state.daily_quote_count}/{daily_limit}")

    # All checks passed
    print("\n🎉 ALL CHECKS PASSED - PUBLISH QUOTE")
    print("="*70 + "\n")
    return True, f"Window '{active_window.name}' active and all checks passed"


def should_publish_reel(force_publish: bool = False) -> Tuple[bool, str]:
    """
    Determine if a reel should be published now
    Returns: (should_publish, reason)
    """
    # Off-day / pause toggle check. A paused day blocks reels unless an explicit
    # force_publish is requested. Checked before the manual dispatch override.
    if not force_publish:
        paused, pause_reason = _paused_reason()
        if paused:
            print("⏸️ REEL publishing is paused today:")
            print(f"   ↳ {pause_reason}")
            return False, f"Paused: {pause_reason}"

    if is_manual_dispatch_trigger():
        print("\n" + "="*70)
        print("⚡ MANUAL DISPATCH OVERRIDE - REEL")
        print("="*70)
        print("Manual workflow_dispatch trigger detected: bypassing all schedule/spacing/day-limit checks")
        return True, "Manual workflow_dispatch trigger: bypassing scheduling checks"

    print("\n" + "="*70)
    print("🎬 REEL SCHEDULER - Decision Process")
    print("="*70)
    
    ist_now = get_ist_now()
    print(f"📅 Current time (IST): {ist_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📆 Weekday: {get_current_weekday().title()}")
    
    # Step 1: Check if we're in a reel window (includes generation time)
    active_window = get_active_window(ContentType.REEL)
    
    if not active_window:
        print("❌ Not in a reel posting window")
        return False, "Not in a reel posting window"
    
    print(f"✅ Active window: {active_window.name} ({active_window.start_hour}:{active_window.start_minute:02d} - {active_window.end_hour}:{active_window.end_minute:02d})")
    print(f"⏰ Reel generation time: {REEL_GENERATION_TIME} minutes")
    
    # Step 2: Check if this slot is already completed
    state = get_scheduler_state()
    
    # Smart scheduling backstops - never post at odd hours, and if an earlier
    # slot today was missed, suppress the final slot so a delay never cascades
    # into an off-hours post (e.g. a reel finishing at 1 AM IST).
    if not is_within_safe_publishing_hours(ContentType.REEL, ist_now):
        print('❌ Outside safe publishing hours (reel would finish past 21:00 IST); skipping to avoid an odd-hour post.')
        return False, f'Outside safe publishing hours (IST {ist_now.hour:02d}:{ist_now.minute:02d})'
    if (not force_publish
            and _has_earlier_missed_post(ist_now, state, active_window)
            and _is_final_pending_window(active_window, ist_now, state)):
        print(f'❌ An earlier post was missed today; suppressing final reel slot {active_window.name!r}.')
        return False, 'Earlier post missed today; final-slot suppressed (smart-skip rule)'
    
    if active_window.name in state.completed_slots:
        print(f"❌ Slot '{active_window.name}' already completed today")
        return False, f"Slot '{active_window.name}' already completed today"

    blocked, lock_reason = _active_job_blocks(state)
    if blocked:
        print(f"❌ {lock_reason}")
        return False, lock_reason
    
    print(f"✅ Slot '{active_window.name}' not yet completed")
    
    # Step 3: Check minimum spacing
    minutes_since = minutes_since_last_post()
    
    if minutes_since is not None and minutes_since < MIN_SPACING_MINUTES:
        remaining = MIN_SPACING_MINUTES - minutes_since
        print(f"❌ Too soon after last post ({minutes_since} min ago, need {MIN_SPACING_MINUTES} min)")
        return False, f"Need {remaining} more minutes before next post"
    
    if minutes_since is not None:
        print(f"✅ Sufficient spacing: {minutes_since} minutes since last post")
    else:
        print(f"✅ No recent posts found - OK to post")
    
    # Step 4: Check daily limits (event-aware)
    daily_limit = _get_event_daily_limit(ContentType.REEL)
    if state.daily_reel_count >= daily_limit:
        print(f"❌ Daily reel limit reached ({state.daily_reel_count}/{daily_limit})")
        return False, f"Daily reel limit ({daily_limit}) reached"
    
    print(f"✅ Daily reel count: {state.daily_reel_count}/{daily_limit}")
    
    # All checks passed
    print("\n🎉 ALL CHECKS PASSED - START REEL GENERATION")
    print(f"⏰ Note: Generation takes ~{REEL_GENERATION_TIME} min, video will publish within window")
    print("="*70 + "\n")
    return True, f"Window '{active_window.name}' active and all checks passed"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_schedule_summary() -> None:
    """Print a summary of today's schedule"""
    weekday = get_current_weekday()
    windows = WEEKLY_SCHEDULE.get(weekday, [])
    state = get_scheduler_state()
    
    # Get event-aware daily limits
    quote_limit = _get_event_daily_limit(ContentType.QUOTE)
    reel_limit = _get_event_daily_limit(ContentType.REEL)
    
    print("\n" + "="*70)
    print(f"📅 TODAY'S SCHEDULE ({weekday.title()})")
    print("="*70)
    
    quote_windows = [w for w in windows if w.content_type == ContentType.QUOTE]
    reel_windows = [w for w in windows if w.content_type == ContentType.REEL]
    
    print(f"\n📝 QUOTES ({len(quote_windows)} windows, {state.daily_quote_count}/{quote_limit} completed):")
    for w in quote_windows:
        status = "✅ DONE" if w.name in state.completed_slots else "⏳ PENDING"
        print(f"  {status} {w.name}: {w.start_hour}:{w.start_minute:02d} - {w.end_hour}:{w.end_minute:02d}")
    
    print(f"\n🎬 REELS ({len(reel_windows)} windows, {state.daily_reel_count}/{reel_limit} completed):")
    for w in reel_windows:
        status = "✅ DONE" if w.name in state.completed_slots else "⏳ PENDING"
        gen_start_min = w.start_minutes() - REEL_GENERATION_TIME
        gen_start_h = gen_start_min // 60
        gen_start_m = gen_start_min % 60
        print(f"  {status} {w.name}:")
        print(f"      Generation starts: {gen_start_h}:{gen_start_m:02d}")
        print(f"      Publish window: {w.start_hour}:{w.start_minute:02d} - {w.end_hour}:{w.end_minute:02d}")
        print(f"      Priority: {w.priority}/5")
    
    if state.active_job:
        stale_label = "STALE" if _active_job_is_stale(state.active_job) else "RUNNING"
        print(f"\n🔒 Active job ({stale_label}): {state.active_job}")

    print("\n" + "="*70 + "\n")


def create_scheduler_gist() -> Optional[str]:
    """Helper to create a new gist for scheduler state"""
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set")
        return None
    
    try:
        print("🆕 Creating new GitHub Gist for scheduler state...")
        
        url = "https://api.github.com/gists"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        initial_state = _default_scheduler_state()
        
        payload = {
            "description": "Aesthetic Vibes - Smart Scheduler State",
            "public": False,
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps(asdict(initial_state), indent=2)
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 201:
            gist_data = response.json()
            gist_id = gist_data["id"]
            gist_url = gist_data["html_url"]
            
            print(f"✅ Gist created successfully!")
            print(f"📋 GIST ID: {gist_id}")
            print(f"🔗 URL: {gist_url}")
            print(f"\n⚠️ IMPORTANT: Add this to your secrets:")
            print(f"   SCHEDULER_GIST_ID={gist_id}")
            
            return gist_id
        else:
            print(f"❌ Failed to create gist: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating gist: {e}")
        return None


# ============================================================================
# MAIN - CLI (off-day toggle) / TEST
# ============================================================================

def _print_pause_config() -> None:
    cfg = get_pause_config()
    print("\n" + "="*50)
    print("⏸️  DATE-PAUSE CONFIG")
    print("="*50)
    paused = cfg['paused_dates'] or []
    print(f"  Today ({cfg['today']})  : {'PAUSED - all posts skipped' if cfg['paused_today'] else 'ACTIVE - normal flow'}")
    print(f"  Paused dates   : {', '.join(paused) or 'none'}")
    print("="*50 + "\n")


def _run_pause_cli(args: List[str]) -> int:
    """Handle the date-pause toggle CLI and return a process exit code."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="smart_scheduler",
        description="Pause/resume ALL publishing for one day via the Pause Manager logic.",
    )
    parser.add_argument("--to", choices=["on", "off"],
                        help="'on' = skip all posts that day, 'off' = resume normal flow")
    parser.add_argument("--date", default="",
                        help="Optional date YYYY-MM-DD. If omitted, today (IST) is used.")
    parser.add_argument("--status", action="store_true",
                        help="Show the current pause configuration")

    parsed = parser.parse_args(args)

    if not parsed.to and not parsed.status:
        _print_pause_config()
        return 0

    if parsed.status:
        _print_pause_config()
        return 0

    ok, msg = set_pause_day(parsed.date, parsed.to == "on")
    print(("✅ " if ok else "❌ ") + msg)
    if not ok:
        return 1

    _print_pause_config()
    return 0


if __name__ == "__main__":
    import sys

    # If the user passed toggle arguments, run the CLI mode instead of the test.
    if len(sys.argv) > 1:
        sys.exit(_run_pause_cli(sys.argv[1:]))

    print("\n🧪 SMART SCHEDULER TEST\n")
    
    # Show today's schedule
    get_schedule_summary()
    
    # Show off-day / pause status up front so a paused day is obvious in logs.
    _print_pause_config()
    
    # Test quote decision
    should_post, reason = should_publish_quote()
    print(f"\n📝 Quote Decision: {'✅ PUBLISH' if should_post else '❌ SKIP'}")
    print(f"   Reason: {reason}")
    
    # Test reel decision
    should_post, reason = should_publish_reel()
    print(f"\n🎬 Reel Decision: {'✅ PUBLISH' if should_post else '❌ SKIP'}")
    print(f"   Reason: {reason}")
    
    print("\n✅ Test complete\n")

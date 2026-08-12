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

from datetime import datetime, timedelta, timezone
import json
import requests
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

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
WINDOW_GRACE_PERIOD = 30  # Minutes after window closes to still publish
QUOTE_LOOKAHEAD_MINUTES = 5  # Small buffer before a quote window starts, not a random publish time
MISSED_WINDOW_RECOVERY_MINUTES = 90  # Allow a late quote recovery after a recent missed window
ACTIVE_JOB_TIMEOUT_MINUTES = 60  # Clear stale generation locks after this time


class ContentType(Enum):
    QUOTE = "quote"
    REEL = "reel"


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

WEEKLY_SCHEDULE: Dict[str, List[PostingWindow]] = {
    "monday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 9, 0, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 12, 45, 14, 0, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 18, 30, 19, 30, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 21, 0, priority=5),
        PostingWindow("late_reel", ContentType.REEL, 22, 15, 23, 15, priority=4),
    ],
    "tuesday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 9, 0, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 13, 0, 14, 0, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 18, 30, 19, 30, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 21, 0, priority=5),
        PostingWindow("late_reel", ContentType.REEL, 22, 15, 23, 15, priority=4),
    ],
    "wednesday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 9, 0, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 13, 0, 14, 0, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 18, 30, 19, 30, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 21, 15, priority=5),
        PostingWindow("late_reel", ContentType.REEL, 22, 15, 23, 15, priority=4),
    ],
    "thursday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 9, 0, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 13, 0, 14, 0, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 18, 30, 19, 30, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 21, 15, priority=5),
        PostingWindow("late_reel", ContentType.REEL, 22, 15, 23, 15, priority=4),
    ],
    "friday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 8, 0, 9, 0, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 13, 0, 14, 15, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 18, 15, 19, 15, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 15, 21, 30, priority=5),
        PostingWindow("late_reel", ContentType.REEL, 22, 30, 23, 30, priority=4),
    ],
    "saturday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 10, 0, 11, 0, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 15, 0, 16, 15, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 18, 45, 19, 45, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 30, 21, 45, priority=5),
        PostingWindow("late_reel", ContentType.REEL, 22, 45, 23, 45, priority=4),
    ],
    "sunday": [
        PostingWindow("morning_quote", ContentType.QUOTE, 9, 30, 10, 30, priority=3),
        PostingWindow("afternoon_reel", ContentType.REEL, 15, 30, 16, 45, priority=4),
        PostingWindow("evening_quote", ContentType.QUOTE, 18, 30, 19, 30, priority=3),
        PostingWindow("prime_reel", ContentType.REEL, 20, 0, 21, 15, priority=5),
        PostingWindow("late_reel", ContentType.REEL, 22, 0, 23, 0, priority=4),
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


def _today_key() -> str:
    """Return today's date in IST, because posting windows are IST based."""
    ist_offset = timedelta(hours=5, minutes=30)
    return (datetime.now(timezone.utc) + ist_offset).strftime("%Y-%m-%d")


def _default_scheduler_state(previous: Optional[dict] = None) -> SchedulerState:
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
    )


def _state_from_dict(state_dict: dict) -> SchedulerState:
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


def mark_slot_completed(window: PostingWindow):
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
# FACEBOOK API - CHECK RECENT POSTS
# ============================================================================

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


def get_active_window(content_type: ContentType) -> Optional[PostingWindow]:
    """
    Get the currently active window for this content type.
    Returns None if no window is active or approaching.
    """
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
    
    # Step 4: Check daily limits
    if state.daily_quote_count >= 2:
        print(f"❌ Daily quote limit reached ({state.daily_quote_count}/2)")
        return False, "Daily quote limit (2) reached"
    
    print(f"✅ Daily quote count: {state.daily_quote_count}/2")
    
    # All checks passed
    print("\n🎉 ALL CHECKS PASSED - PUBLISH QUOTE")
    print("="*70 + "\n")
    return True, f"Window '{active_window.name}' active and all checks passed"


def should_publish_reel(force_publish: bool = False) -> Tuple[bool, str]:
    """
    Determine if a reel should be published now
    Returns: (should_publish, reason)
    """
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
    
    # Step 4: Check daily limits
    if state.daily_reel_count >= 3:
        print(f"❌ Daily reel limit reached ({state.daily_reel_count}/3)")
        return False, "Daily reel limit (3) reached"
    
    print(f"✅ Daily reel count: {state.daily_reel_count}/3")
    
    # All checks passed
    print("\n🎉 ALL CHECKS PASSED - START REEL GENERATION")
    print(f"⏰ Note: Generation takes ~{REEL_GENERATION_TIME} min, video will publish within window")
    print("="*70 + "\n")
    return True, f"Window '{active_window.name}' active and all checks passed"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_schedule_summary():
    """Print a summary of today's schedule"""
    weekday = get_current_weekday()
    windows = WEEKLY_SCHEDULE.get(weekday, [])
    state = get_scheduler_state()
    
    print("\n" + "="*70)
    print(f"📅 TODAY'S SCHEDULE ({weekday.title()})")
    print("="*70)
    
    quote_windows = [w for w in windows if w.content_type == ContentType.QUOTE]
    reel_windows = [w for w in windows if w.content_type == ContentType.REEL]
    
    print(f"\n📝 QUOTES ({len(quote_windows)} windows, {state.daily_quote_count} completed):")
    for w in quote_windows:
        status = "✅ DONE" if w.name in state.completed_slots else "⏳ PENDING"
        print(f"  {status} {w.name}: {w.start_hour}:{w.start_minute:02d} - {w.end_hour}:{w.end_minute:02d}")
    
    print(f"\n🎬 REELS ({len(reel_windows)} windows, {state.daily_reel_count} completed):")
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


def create_scheduler_gist():
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
# MAIN - FOR TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 SMART SCHEDULER TEST\n")
    
    # Show today's schedule
    get_schedule_summary()
    
    # Test quote decision
    should_post, reason = should_publish_quote()
    print(f"\n📝 Quote Decision: {'✅ PUBLISH' if should_post else '❌ SKIP'}")
    print(f"   Reason: {reason}")
    
    # Test reel decision
    should_post, reason = should_publish_reel()
    print(f"\n🎬 Reel Decision: {'✅ PUBLISH' if should_post else '❌ SKIP'}")
    print(f"   Reason: {reason}")
    
    print("\n✅ Test complete\n")

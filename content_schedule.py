"""
content_schedule.py - Smart randomized content type selection

Ensures maximum diversity throughout the week with time-appropriate energy.

The scheduler has only two active quote slots:
    - MORNING: 5 AM - 5 PM IST
    - EVENING: 5 PM - 5 AM IST

The original afternoon content types are split between the
morning and evening pools so ALL content types remain selectable.

History is stored in GitHub Gist for synchronized usage across
GitHub Actions runs.
"""

from datetime import datetime, timezone
import random

from gist_storage import get_content_history, add_to_history


# ============================================================================
# ORIGINAL CONTENT TYPES
# ============================================================================

MORNING_ENERGY_TYPES = [
    {"type": "MOTIVATIONAL_INSPIRING", "name": "Motivational/Inspiring"},
    {"type": "ELDER_WISDOM", "name": "Elder Wisdom"},
    {"type": "GRATITUDE_MINDFUL", "name": "Gratitude/Mindful"},
    {"type": "SUCCESS_HUSTLE", "name": "Success/Hustle"},
    {"type": "DREAMS_AMBITIONS", "name": "Dreams & Ambitions"},
    {"type": "LIFE_LESSONS_SUGGESTIONS", "name": "Life Lessons"},
    {"type": "SMALL_VICTORIES", "name": "Small Victories"},
    {"type": "MUSIC_ART_SOUL", "name": "Music & Art"},
]


# Originally afternoon content.
# Since the scheduler only has morning/evening slots,
# these are split between the two active pools.
AFTERNOON_RELATABLE_TYPES = [
    {"type": "FUNNY_SASSY", "name": "Funny/Sassy"},
    {"type": "BITTERSWEET_RELATABLE", "name": "Bittersweet Relatable"},
    {"type": "HE_SHE_RELATIONSHIP", "name": "He/She Relationship"},
    {"type": "POP_CULTURE_LYRICS", "name": "Pop Culture/Lyrics"},
    {"type": "DAILY_STRUGGLE_HUMOR", "name": "Daily Struggle Humor"},
    {"type": "FOOD_COMFORT", "name": "Food & Comfort"},
    {"type": "SOCIAL_COMMENTARY", "name": "Social Commentary"},
    {"type": "FRIENDSHIP_BONDS", "name": "Friendship & Bonds"},
    {"type": "WHOLESOME_JOY", "name": "Wholesome/Joy"},
]


EVENING_DEEP_TYPES = [
    {"type": "DEEP_EMOTIONAL", "name": "Deep Emotional"},
    {"type": "NATURE_UNIVERSE", "name": "Nature/Universe"},
    {"type": "LIFE_WISDOM", "name": "Life Wisdom"},
    {"type": "ONE_LINER", "name": "One-Liner"},
    {"type": "THINGS_NOBODY_TALKS_ABOUT", "name": "Hidden Truths"},
    {"type": "UNPOPULAR_OPINION", "name": "Unpopular Opinion"},
    {"type": "CHILDHOOD_VS_NOW", "name": "Childhood vs Now"},
    {"type": "SELF_LOVE_BOUNDARIES", "name": "Self-Love & Boundaries"},
    {"type": "MENTAL_HEALTH_REAL", "name": "Mental Health Real Talk"},
    {"type": "PHILOSOPHICAL_LIGHT", "name": "Philosophical Light"},
    {"type": "OVERTHINKING_ANXIETY", "name": "Overthinking/Anxiety"},
    {"type": "GROWTH_HEALING", "name": "Growth & Healing"},
    {"type": "LATE_NIGHT_THOUGHTS", "name": "Late Night Thoughts"},
    {"type": "FORGIVENESS_LETTING_GO", "name": "Forgiveness & Letting Go"},
    {"type": "TIME_PERSPECTIVE", "name": "Time Perspective"},
    {"type": "TRUTH_BOMBS", "name": "Truth Bombs"},
    {"type": "TRAVEL_WANDERLUST", "name": "Travel/Wanderlust"},
]


# ============================================================================
# AFTERNOON CONTENT SPLIT
# ============================================================================

# 5 afternoon types added to the morning pool.
AFTERNOON_TO_MORNING_TYPES = [
    AFTERNOON_RELATABLE_TYPES[0],  # FUNNY_SASSY
    AFTERNOON_RELATABLE_TYPES[3],  # POP_CULTURE_LYRICS
    AFTERNOON_RELATABLE_TYPES[4],  # DAILY_STRUGGLE_HUMOR
    AFTERNOON_RELATABLE_TYPES[5],  # FOOD_COMFORT
    AFTERNOON_RELATABLE_TYPES[8],  # WHOLESOME_JOY
]


# 4 afternoon types added to the evening pool.
AFTERNOON_TO_EVENING_TYPES = [
    AFTERNOON_RELATABLE_TYPES[1],  # BITTERSWEET_RELATABLE
    AFTERNOON_RELATABLE_TYPES[2],  # HE_SHE_RELATIONSHIP
    AFTERNOON_RELATABLE_TYPES[6],  # SOCIAL_COMMENTARY
    AFTERNOON_RELATABLE_TYPES[7],  # FRIENDSHIP_BONDS
]


# ============================================================================
# ACTIVE QUOTE POOLS
# ============================================================================

# 8 original morning + 5 afternoon = 13
MORNING_QUOTE_TYPES = (
    MORNING_ENERGY_TYPES
    + AFTERNOON_TO_MORNING_TYPES
)


# 17 original evening + 4 afternoon = 21
EVENING_QUOTE_TYPES = (
    EVENING_DEEP_TYPES
    + AFTERNOON_TO_EVENING_TYPES
)


# All 34 content types.
ALL_CONTENT_TYPES = (
    MORNING_ENERGY_TYPES
    + AFTERNOON_RELATABLE_TYPES
    + EVENING_DEEP_TYPES
)


ALL_CONTENT_TYPE_COUNT = len({
    content_info["type"]
    for content_info in ALL_CONTENT_TYPES
})


# ============================================================================
# INTERNAL VALIDATION
# ============================================================================

def validate_content_types():
    """
    Validate the scheduler itself.

    Checks:
        - No duplicate content types
        - Every type is in an active pool
        - No type appears in both active pools
        - All afternoon types are assigned
    """

    all_types = [
        content_info["type"]
        for content_info in ALL_CONTENT_TYPES
    ]

    morning_types = {
        content_info["type"]
        for content_info in MORNING_QUOTE_TYPES
    }

    evening_types = {
        content_info["type"]
        for content_info in EVENING_QUOTE_TYPES
    }

    afternoon_types = {
        content_info["type"]
        for content_info in AFTERNOON_RELATABLE_TYPES
    }

    # Check duplicates in master list.
    if len(all_types) != len(set(all_types)):
        duplicates = sorted({
            content_type
            for content_type in all_types
            if all_types.count(content_type) > 1
        })

        raise ValueError(
            f"Duplicate content types found: {duplicates}"
        )

    # Check that every type exists in an active pool.
    active_types = morning_types | evening_types

    missing_from_active_pools = (
        set(all_types) - active_types
    )

    if missing_from_active_pools:
        raise ValueError(
            "Content types missing from active pools: "
            f"{sorted(missing_from_active_pools)}"
        )

    # Check that morning/evening don't overlap.
    overlap = morning_types & evening_types

    if overlap:
        raise ValueError(
            "Content types appear in BOTH morning and evening pools: "
            f"{sorted(overlap)}"
        )

    # Check that all afternoon types were assigned.
    afternoon_in_active = (
        morning_types | evening_types
    ) & afternoon_types

    missing_afternoon = (
        afternoon_types - afternoon_in_active
    )

    if missing_afternoon:
        raise ValueError(
            "Afternoon types not assigned to an active pool: "
            f"{sorted(missing_afternoon)}"
        )

    print(
        f"✅ Scheduler validation passed: "
        f"{len(all_types)} unique content types"
    )


validate_content_types()


# ============================================================================
# TIME CATEGORY
# ============================================================================

def get_time_category():
    """
    Determine quote category based on current IST time.

    Returns:
        tuple:
            ("MORNING", MORNING_QUOTE_TYPES)
            or
            ("EVENING", EVENING_QUOTE_TYPES)
    """

    now_utc = datetime.now(timezone.utc)

    # Convert UTC to IST (UTC + 5:30).
    ist_hour = (
        now_utc.hour
        + 5
        + (now_utc.minute + 30) // 60
    ) % 24

    # 5 AM - 5 PM IST
    if 5 <= ist_hour < 17:
        return "MORNING", MORNING_QUOTE_TYPES

    # 5 PM - 5 AM IST
    return "EVENING", EVENING_QUOTE_TYPES


# ============================================================================
# CONTENT TYPE SELECTION
# ============================================================================

def get_content_type_for_time(record_history=True):
    """
    Randomly select an appropriate content type based on time.

    Smart weighting:
        - Not used in last 10 posts -> weight 3
        - Used 6-10 posts ago -> weight 2
        - Used in last 5 posts -> weight 1

    Args:
        record_history:
            True:
                Immediately save selected type.

            False:
                Do not update history.
                Useful when history should only be updated
                after successful upload.

    Returns:
        dict containing:
            type
            name
            reason
    """

    time_label, available_types = get_time_category()

    history = get_content_history() or []

    # Last 10 posts are used for repetition control.
    recent_types = history[-10:]

    weighted_types = []

    for content_info in available_types:
        content_type = content_info["type"]

        if content_type not in recent_types:
            # Not used in the last 10 posts.
            weighted_types.extend([content_info] * 3)

        elif content_type in recent_types[-5:]:
            # Used in the last 5 posts.
            weighted_types.append(content_info)

        else:
            # Used 6-10 posts ago.
            weighted_types.extend([content_info] * 2)

    # Safety fallback.
    if not weighted_types:
        weighted_types = available_types

    selected = random.choice(weighted_types)

    if record_history:
        add_to_history(selected["type"])

    result = {
        "type": selected["type"],
        "name": selected["name"],
        "reason": (
            f"{time_label} energy - "
            "randomly selected for maximum variety"
        ),
    }

    print(f"⏰ Time Category: {time_label}")
    print(
        f"📝 Selected: "
        f"{result['name']} ({result['type']})"
    )
    print(f"💡 Reason: {result['reason']}")

    print(
    f"📊 Recent types: "
    f"{', '.join(recent_types[-5:]) if recent_types else 'None'}"
    )

    if not record_history:
        print(
            "📌 Content history will be updated "
            "after successful upload"
        )

    return result


# ============================================================================
# SUMMARY
# ============================================================================

def get_all_types_summary():
    """Print summary of all content types and active pools."""

    print("\n" + "=" * 70)

    print(
        f"SMART RANDOMIZED CONTENT SYSTEM - "
        f"{ALL_CONTENT_TYPE_COUNT} DIVERSE TYPES"
    )

    print("=" * 70)

    # Morning
    print(
        f"\n🌅 ACTIVE MORNING QUOTE POOL "
        f"(5 AM - 5 PM IST) - "
        f"{len(MORNING_QUOTE_TYPES)} Types:"
    )

    for i, info in enumerate(MORNING_QUOTE_TYPES, 1):
        print(
            f"  {i:2}. "
            f"{info['name']} "
            f"({info['type']})"
        )

    # Evening
    print(
        f"\n🌙 ACTIVE EVENING QUOTE POOL "
        f"(5 PM - 5 AM IST) - "
        f"{len(EVENING_QUOTE_TYPES)} Types:"
    )

    for i, info in enumerate(EVENING_QUOTE_TYPES, 1):
        print(
            f"  {i:2}. "
            f"{info['name']} "
            f"({info['type']})"
        )

    # Afternoon split
    print(
        "\n📌 ORIGINAL AFTERNOON TYPES "
        "SPLIT BETWEEN MORNING AND EVENING:"
    )

    print("\n  Morning gets:")
    for info in AFTERNOON_TO_MORNING_TYPES:
        print(
            f"    • {info['name']} "
            f"({info['type']})"
        )

    print("\n  Evening gets:")
    for info in AFTERNOON_TO_EVENING_TYPES:
        print(
            f"    • {info['name']} "
            f"({info['type']})"
        )

    # Totals
    print("\n📊 TOTALS:")
    print(
        f"  Original morning types:   "
        f"{len(MORNING_ENERGY_TYPES)}"
    )
    print(
        f"  Original afternoon types: "
        f"{len(AFTERNOON_RELATABLE_TYPES)}"
    )
    print(
        f"  Original evening types:   "
        f"{len(EVENING_DEEP_TYPES)}"
    )
    print(
        f"  Total unique types:       "
        f"{ALL_CONTENT_TYPE_COUNT}"
    )
    print(
        f"  Active morning pool:      "
        f"{len(MORNING_QUOTE_TYPES)}"
    )
    print(
        f"  Active evening pool:      "
        f"{len(EVENING_QUOTE_TYPES)}"
    )

    print("\n" + "=" * 70)

    print(
        "✅ SMART RANDOMIZATION: "
        "Avoids recent repeats (last 10 posts)"
    )

    print(
        "✅ MORNING COVERAGE: "
        "13 content types available"
    )

    print(
        "✅ EVENING COVERAGE: "
        "21 content types available"
    )

    print(
        "✅ COMPLETE COVERAGE: "
        f"All {ALL_CONTENT_TYPE_COUNT} types are selectable"
    )

    print(
        "✅ GITHUB ACTIONS: "
        "History synchronized through GitHub Gist"
    )

    print("=" * 70 + "\n")


# ============================================================================
# STATISTICS
# ============================================================================

def get_stats():
    """Show statistics about recent content variety."""

    history = get_content_history()

    if not history:
        print("📊 No history yet")
        return

    from collections import Counter

    counts = Counter(history)

    print(
        f"\n📊 CONTENT VARIETY STATS "
        f"(Last {len(history)} posts):"
    )

    print("=" * 50)

    print("\nMost Used Types:")

    for content_type, count in counts.most_common(5):
        print(
            f"  • {content_type}: "
            f"{count} times"
        )

    print(
        f"\nTotal Unique Types Used: "
        f"{len(counts)} / {ALL_CONTENT_TYPE_COUNT}"
    )

    if counts:
        print(
            f"Average posts per type: "
            f"{len(history) / len(counts):.1f}"
        )

    print("=" * 50 + "\n")


# ============================================================================
# MAIN TEST
# ============================================================================

if __name__ == "__main__":

    get_all_types_summary()

    print("\n🕐 CURRENT TIME TEST:")

    content_info = get_content_type_for_time()

    print(
        f"\n✅ Selected: "
        f"{content_info['name']}"
    )

    print(
        f"📝 Type: "
        f"{content_info['type']}"
    )

    get_stats()
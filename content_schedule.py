"""
content_schedule.py - Smart randomized content type selection
Ensures maximum diversity throughout the week with time-appropriate energy
Uses GitHub Gist for synchronized history storage (no local files)
"""

from datetime import datetime, timezone
import random
from gist_storage import get_content_history, add_to_history

# ALL 35 CONTENT TYPES organized by energy level and time appropriateness
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

AFTERNOON_RELATABLE_TYPES = [
    {"type": "FUNNY_SASSY", "name": "Funny/Sassy"},
    {"type": "BITTERSWEET_RELATABLE", "name": "Bittersweet Relatable"},
    {"type": "SHORT_CONVERSATION", "name": "Short Conversation"},
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

# Quote scheduler has only morning and evening quote slots.
# Split afternoon content 5/5 so every content type can still be selected.
AFTERNOON_TO_MORNING_TYPES = [
    AFTERNOON_RELATABLE_TYPES[0],  # FUNNY_SASSY
    AFTERNOON_RELATABLE_TYPES[4],  # POP_CULTURE_LYRICS
    AFTERNOON_RELATABLE_TYPES[5],  # DAILY_STRUGGLE_HUMOR
    AFTERNOON_RELATABLE_TYPES[6],  # FOOD_COMFORT
    AFTERNOON_RELATABLE_TYPES[9],  # WHOLESOME_JOY
]

AFTERNOON_TO_EVENING_TYPES = [
    AFTERNOON_RELATABLE_TYPES[1],  # BITTERSWEET_RELATABLE
    AFTERNOON_RELATABLE_TYPES[2],  # SHORT_CONVERSATION
    AFTERNOON_RELATABLE_TYPES[3],  # HE_SHE_RELATIONSHIP
    AFTERNOON_RELATABLE_TYPES[7],  # SOCIAL_COMMENTARY
    AFTERNOON_RELATABLE_TYPES[8],  # FRIENDSHIP_BONDS
]

MORNING_QUOTE_TYPES = MORNING_ENERGY_TYPES + AFTERNOON_TO_MORNING_TYPES
EVENING_QUOTE_TYPES = EVENING_DEEP_TYPES + AFTERNOON_TO_EVENING_TYPES
ALL_CONTENT_TYPES = MORNING_ENERGY_TYPES + AFTERNOON_RELATABLE_TYPES + EVENING_DEEP_TYPES
ALL_CONTENT_TYPE_COUNT = len({content_info["type"] for content_info in ALL_CONTENT_TYPES})


def get_time_category():
    """Determine quote category based on UTC hour (converted to IST)."""
    now_utc = datetime.now(timezone.utc)
    
    # Convert UTC to IST (UTC + 5:30)
    ist_hour = (now_utc.hour + 5 + (now_utc.minute + 30) // 60) % 24
    
    # Scheduled quotes run in morning/evening only.
    # Afternoon manual runs use the merged morning pool so no type is isolated.
    if 5 <= ist_hour < 17:  # 5 AM - 5 PM IST
        return "MORNING", MORNING_QUOTE_TYPES
    else:  # 5 PM - 5 AM IST
        return "EVENING", EVENING_QUOTE_TYPES


def get_content_type_for_time(record_history=True):
    """
    Randomly select appropriate content type based on time, avoiding recent repeats.

    Args:
        record_history: Keep True for current behavior. Set False when caller wants
                        to add to CONTENT_HISTORY_GIST_ID only after upload success.

    Returns: dict with type, name, and reason
    """
    # Get current time category
    time_label, available_types = get_time_category()
    
    # Load history from GitHub Gist to avoid repetition
    history = get_content_history()
    recent_types = history[-10:]  # Last 10 posts
    
    # Filter out recently used types (smart weighting)
    weighted_types = []
    for content_info in available_types:
        content_type = content_info["type"]
        
        # Count how recently this type was used
        if content_type not in recent_types:
            # Not used recently - full weight (add 3 times)
            weighted_types.extend([content_info] * 3)
        elif content_type in recent_types[-5:]:
            # Used in last 5 posts - very low weight (add 1 time)
            weighted_types.append(content_info)
        else:
            # Used 6-10 posts ago - medium weight (add 2 times)
            weighted_types.extend([content_info] * 2)
    
    # Randomly select from weighted pool
    selected = random.choice(weighted_types if weighted_types else available_types)
    
    if record_history:
        # Existing behavior for manual/legacy callers.
        add_to_history(selected["type"])
    
    # Prepare response
    result = {
        "type": selected["type"],
        "name": selected["name"],
        "reason": f"{time_label} energy - randomly selected for maximum variety"
    }
    
    print(f"⏰ Time Category: {time_label}")
    print(f"📝 Selected: {result['name']} ({result['type']})")
    print(f"💡 Reason: {result['reason']}")
    print(f"📊 Recent types: {', '.join(recent_types[-5:]) if recent_types else 'None'}")
    if not record_history:
        print("📌 Content history will be updated after successful upload")
    
    return result
    

def get_all_types_summary():
    """Print summary of all content types organized by original and active quote pools."""
    print("\n" + "="*70)
    print(f"SMART RANDOMIZED CONTENT SYSTEM - {ALL_CONTENT_TYPE_COUNT} DIVERSE TYPES")
    print("="*70)
    
    print(f"\n🌅 ACTIVE MORNING QUOTE POOL (5 AM - 5 PM IST) - {len(MORNING_QUOTE_TYPES)} Types:")
    for i, info in enumerate(MORNING_QUOTE_TYPES, 1):
        print(f"  {i}. {info['name']}")
    
    print(f"\n🌙 ACTIVE EVENING QUOTE POOL (5 PM - 5 AM IST) - {len(EVENING_QUOTE_TYPES)} Types:")
    for i, info in enumerate(EVENING_QUOTE_TYPES, 1):
        print(f"  {i}. {info['name']}")
    
    print("\n📌 Original afternoon types were split 5/5:")
    print("  Morning gets:")
    for info in AFTERNOON_TO_MORNING_TYPES:
        print(f"    • {info['name']}")
    print("  Evening gets:")
    for info in AFTERNOON_TO_EVENING_TYPES:
        print(f"    • {info['name']}")
    
    print("\n" + "="*70)
    print("✅ SMART RANDOMIZATION: Avoids recent repeats (last 10 posts)")
    print("✅ MORNING/EVENING COVERAGE: All content types can be used by scheduled quotes")
    print(f"✅ MAXIMUM VARIETY: {ALL_CONTENT_TYPE_COUNT} types ensure nothing gets missed weekly")
    print("✅ WORKS WITH GITHUB ACTIONS: No strict timing required")
    print("="*70 + "\n")


def get_stats():
    """Show statistics about recent content variety"""
    history = get_content_history()
    if not history:
        print("📊 No history yet")
        return
    
    print(f"\n📊 CONTENT VARIETY STATS (Last {len(history)} posts):")
    print("="*50)
    
    # Count frequency
    from collections import Counter
    counts = Counter(history)
    
    print("\nMost Used Types:")
    for content_type, count in counts.most_common(5):
        print(f"  • {content_type}: {count} times")
    
    print(f"\nTotal Unique Types Used: {len(counts)} / {ALL_CONTENT_TYPE_COUNT}")
    print(f"Average posts per type: {len(history) / len(counts):.1f}")
    print("="*50 + "\n")


if __name__ == "__main__":
    # Show all available types
    get_all_types_summary()
    
    # Test current time selection
    print("\n🕐 CURRENT TIME TEST:")
    content_info = get_content_type_for_time()
    print(f"\n✅ Selected: {content_info['name']}")
    print(f"📝 Type: {content_info['type']}")
    
    # Show stats if history exists
    get_stats()

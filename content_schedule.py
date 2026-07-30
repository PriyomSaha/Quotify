"""
content_schedule.py - Smart randomized content type selection
Ensures maximum diversity throughout the week with time-appropriate energy
Uses GitHub Gist for synchronized history storage (no local files)
"""

from datetime import datetime, timezone
import random
from gist_storage import get_content_history, add_to_history

# ALL 33 CONTENT TYPES organized by energy level and time appropriateness
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





def get_time_category():
    """Determine time category based on UTC hour (converted to IST)"""
    now_utc = datetime.now(timezone.utc)
    
    # Convert UTC to IST (UTC + 5:30)
    ist_hour = (now_utc.hour + 5 + (now_utc.minute + 30) // 60) % 24
    
    # Time categories based on IST
    if 5 <= ist_hour < 12:  # 5 AM - 12 PM IST
        return "MORNING", MORNING_ENERGY_TYPES
    elif 12 <= ist_hour < 17:  # 12 PM - 5 PM IST
        return "AFTERNOON", AFTERNOON_RELATABLE_TYPES
    else:  # 5 PM - 5 AM IST
        return "EVENING", EVENING_DEEP_TYPES


def get_content_type_for_time():
    """
    Randomly select appropriate content type based on time, avoiding recent repeats
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
    
    # Add to history (saves to Gist automatically)
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
    
    return result
    

def get_all_types_summary():
    """Print summary of all 33 content types organized by time"""
    print("\n" + "="*70)
    print("SMART RANDOMIZED CONTENT SYSTEM - 33 DIVERSE TYPES")
    print("="*70)
    
    print("\n🌅 MORNING ENERGY (5 AM - 12 PM IST) - 8 Types:")
    for i, info in enumerate(MORNING_ENERGY_TYPES, 1):
        print(f"  {i}. {info['name']}")
    
    print("\n☀️ AFTERNOON RELATABLE (12 PM - 5 PM IST) - 10 Types:")
    for i, info in enumerate(AFTERNOON_RELATABLE_TYPES, 1):
        print(f"  {i}. {info['name']}")
    
    print("\n🌙 EVENING DEEP (5 PM - 5 AM IST) - 17 Types:")
    for i, info in enumerate(EVENING_DEEP_TYPES, 1):
        print(f"  {i}. {info['name']}")
    
    print("\n" + "="*70)
    print("✅ SMART RANDOMIZATION: Avoids recent repeats (last 10 posts)")
    print("✅ TIME-APPROPRIATE: Energy matches audience activity")
    print("✅ MAXIMUM VARIETY: 33 types ensure nothing gets missed weekly")
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
    
    print(f"\nTotal Unique Types Used: {len(counts)} / 33")
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

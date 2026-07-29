"""
content_schedule.py - Time-based content type selection
Maps each posting time to a specific content type for variety and appropriate energy
"""

from datetime import datetime, timezone

# 17 unique content types mapped to 17 daily posting times
CONTENT_SCHEDULE = {
    # MORNING ENERGY (6:53 AM - 10:49 AM) - 5 posts
    "01:23": {
        "type": "MOTIVATIONAL_INSPIRING",
        "name": "Motivational/Inspiring",
        "reason": "Start day with positive energy"
    },
    "02:47": {
        "type": "ELDER_WISDOM",
        "name": "Elder Wisdom (Father/Mother used to say)",
        "reason": "Morning family wisdom, relatable to Indian audience"
    },
    "03:11": {
        "type": "FUNNY_SASSY",
        "name": "Funny/Sassy",
        "reason": "Morning humor, lighten up"
    },
    "04:34": {
        "type": "GRATITUDE_MINDFUL",
        "name": "Gratitude/Mindful",
        "reason": "Mid-morning peace"
    },
    "05:19": {
        "type": "SUCCESS_HUSTLE",
        "name": "Success/Hustle",
        "reason": "Work mode motivation"
    },
    
    # AFTERNOON RELATABLE (12:22 PM - 3:37 PM) - 5 posts
    "06:52": {
        "type": "BITTERSWEET_RELATABLE",
        "name": "Bittersweet Relatable Moment",
        "reason": "Lunch break vibes"
    },
    "07:16": {
        "type": "SHORT_CONVERSATION",
        "name": "Short Conversation",
        "reason": "Casual afternoon chat"
    },
    "08:41": {
        "type": "HE_SHE_RELATIONSHIP",
        "name": "He/She Relationship Moment",
        "reason": "Afternoon tea, dating thoughts"
    },
    "09:28": {
        "type": "CHILDHOOD_VS_NOW",
        "name": "Childhood vs Now",
        "reason": "Mid-day nostalgia"
    },
    "10:07": {
        "type": "POP_CULTURE_LYRICS",
        "name": "Pop Culture/Lyrics",
        "reason": "Trending references, energy boost"
    },
    
    # EVENING DEEP (5:19 PM - 10:47 PM) - 7 posts
    "11:49": {
        "type": "NATURE_UNIVERSE",
        "name": "Nature/Universe",
        "reason": "Evening wind down, cosmic perspective"
    },
    "12:22": {
        "type": "LIFE_WISDOM",
        "name": "Life Wisdom",
        "reason": "Evening philosophical thoughts"
    },
    "13:38": {
        "type": "DEEP_EMOTIONAL",
        "name": "Deep Emotional Quote",
        "reason": "Prime time, peak emotional engagement"
    },
    "14:14": {
        "type": "ONE_LINER",
        "name": "One-Liner",
        "reason": "Quotable wisdom"
    },
    "15:56": {
        "type": "THINGS_NOBODY_TALKS_ABOUT",
        "name": "Things Nobody Talks About",
        "reason": "Late night honesty"
    },
    "16:31": {
        "type": "UNPOPULAR_OPINION",
        "name": "Unpopular Opinion",
        "reason": "Night thoughts, controversial"
    },
    "17:17": {
        "type": "WHOLESOME_JOY",
        "name": "Wholesome/Joy",
        "reason": "End day with peace"
    }
}


def get_content_type_for_time():
    """
    Get the appropriate content type based on current UTC time
    Returns: dict with type, name, and reason
    """
    # Get current UTC time (GitHub Actions runs in UTC)
    now_utc = datetime.now(timezone.utc)
    
    # Format as HH:MM to match schedule keys
    current_time = now_utc.strftime("%H:%M")
    
    # Check if current time matches any scheduled time (within 5 min window)
    current_hour = now_utc.hour
    current_minute = now_utc.minute
    
    for scheduled_time, content_info in CONTENT_SCHEDULE.items():
        sched_hour, sched_minute = map(int, scheduled_time.split(':'))
        
        # Match if within 5 minutes of scheduled time
        if current_hour == sched_hour and abs(current_minute - sched_minute) <= 5:
            print(f"✅ Matched time {current_time} to {scheduled_time}")
            print(f"📝 Content type: {content_info['name']}")
            print(f"💡 Reason: {content_info['reason']}")
            return content_info
    
    # Fallback if no exact match (shouldn't happen with proper cron)
    print(f"⚠️ No exact match for {current_time}, using fallback")
    
    # Return based on hour ranges
    if 1 <= current_hour <= 5:
        return CONTENT_SCHEDULE["03:11"]  # Morning funny
    elif 6 <= current_hour <= 10:
        return CONTENT_SCHEDULE["08:41"]  # Afternoon relatable
    else:
        return CONTENT_SCHEDULE["13:38"]  # Evening deep
    

def get_all_types_summary():
    """Print summary of all 17 content types and their timings"""
    print("\n" + "="*60)
    print("CONTENT SCHEDULE - 17 UNIQUE TYPES PER DAY")
    print("="*60)
    
    print("\n🌅 MORNING ENERGY (6:53 AM - 10:49 AM IST):")
    for time_key in ["01:23", "02:47", "03:11", "04:34", "05:19"]:
        info = CONTENT_SCHEDULE[time_key]
        utc_hour = int(time_key.split(':')[0])
        ist_hour = (utc_hour + 5) % 24
        ist_min = (int(time_key.split(':')[1]) + 30) % 60
        print(f"  {ist_hour:02d}:{ist_min:02d} IST - {info['name']}")
    
    print("\n☀️ AFTERNOON RELATABLE (12:22 PM - 3:37 PM IST):")
    for time_key in ["06:52", "07:16", "08:41", "09:28", "10:07"]:
        info = CONTENT_SCHEDULE[time_key]
        utc_hour = int(time_key.split(':')[0])
        ist_hour = (utc_hour + 5) % 24
        ist_min = (int(time_key.split(':')[1]) + 30) % 60
        print(f"  {ist_hour:02d}:{ist_min:02d} IST - {info['name']}")
    
    print("\n🌙 EVENING DEEP (5:19 PM - 10:47 PM IST):")
    for time_key in ["11:49", "12:22", "13:38", "14:14", "15:56", "16:31", "17:17"]:
        info = CONTENT_SCHEDULE[time_key]
        utc_hour = int(time_key.split(':')[0])
        ist_hour = (utc_hour + 5) % 24
        ist_min = (int(time_key.split(':')[1]) + 30) % 60
        print(f"  {ist_hour:02d}:{ist_min:02d} IST - {info['name']}")
    
    print("\n" + "="*60)
    print("✅ NO REPEATING TYPES IN SAME DAY")
    print("✅ TIME-APPROPRIATE ENERGY LEVELS")
    print("✅ PERFECT VARIETY FOR ENGAGEMENT")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test the schedule
    get_all_types_summary()
    
    # Test current time
    print("\n🕐 CURRENT TIME TEST:")
    content_info = get_content_type_for_time()
    print(f"Selected: {content_info['name']}")

#!/usr/bin/env python3
"""
Check when the last post was published on Facebook
Returns minutes since last post
"""

import os
import requests
from datetime import datetime, timezone


def get_minutes_since_last_post():
    """
    Check Facebook page for last post time.
    Returns minutes since last post, or None if error.
    """
    try:
        PAGE_ID = os.getenv("PAGE_ID")
        TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
        API_VERSION = os.getenv("API_VERSION", "v25.0")
        
        if not PAGE_ID or not TOKEN:
            print("⚠️ Missing PAGE_ID or PAGE_ACCESS_TOKEN")
            return None
        
        url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/posts"
        params = {
            "fields": "created_time",
            "limit": 1,
            "access_token": TOKEN,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("data") or len(data["data"]) == 0:
            print("⚠️ No posts found on page")
            return None
        
        last_post = data["data"][0]
        last_time = datetime.fromisoformat(
            last_post["created_time"].replace("Z", "+00:00")
        )
        now = datetime.now(timezone.utc)
        minutes_since = (now - last_time).total_seconds() / 60
        
        print(f"📊 Last post was {minutes_since:.1f} minutes ago")
        return minutes_since
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error checking last post: {e}")
        return None
    except Exception as e:
        print(f"❌ Error checking last post: {e}")
        return None


def should_publish_new_post(min_hours=2):
    """
    Check if enough time has passed to publish a new post.
    
    Args:
        min_hours: Minimum hours required between posts (default 2)
    
    Returns:
        True if should publish, False otherwise
    """
    minutes_since = get_minutes_since_last_post()
    
    if minutes_since is None:
        # If we can't check, skip publishing to be safe
        print(f"⏭️ Skipping publish - unable to verify last post time")
        return False
    
    min_minutes = min_hours * 60
    
    if minutes_since >= min_minutes:
        print(f"✅ {minutes_since:.1f} minutes elapsed (>= {min_hours} hours) - OK to publish")
        return True
    else:
        time_remaining = min_minutes - minutes_since
        print(f"⏳ Only {minutes_since:.1f} minutes elapsed - wait {time_remaining:.1f} more minutes")
        return False


if __name__ == "__main__":
    # Test the function
    from dotenv import load_dotenv
    load_dotenv()
    
    should_publish = should_publish_new_post(min_hours=2)
    print(f"\nShould publish: {should_publish}")

#!/usr/bin/env python3
"""
GitHub Gist storage for content history
Keeps history synchronized between GitHub Actions and Render
No commits to main repo - uses external gist storage
"""

import requests
import json
import os

# Environment variables (set these in GitHub Secrets and Render)
GIST_ID = os.getenv("CONTENT_HISTORY_GIST_ID")  # Your gist ID
GITHUB_TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")  # GitHub personal access token

GIST_FILENAME = "content_history.json"
HISTORY_LIMIT = 30  # Track last 30 posts


def get_content_history():
    """
    Fetch content history from GitHub Gist
    Returns list of recent content types
    """
    if not GIST_ID or not GITHUB_TOKEN:
        print("⚠️ GIST_ID or GITHUB_TOKEN not set - using empty history")
        return []
    
    try:
        print("🔄 Fetching history from GitHub Gist...")
        
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            gist_data = response.json()
            
            # Check if our file exists in the gist
            if GIST_FILENAME in gist_data.get("files", {}):
                content = gist_data["files"][GIST_FILENAME]["content"]
                history = json.loads(content)
                print(f"✅ History loaded: {len(history)} posts")
                return history
            else:
                print("⚠️ History file not found in gist - creating new")
                return []
        else:
            print(f"⚠️ Failed to fetch gist: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Network error fetching history: {e}")
        return []
    except Exception as e:
        print(f"⚠️ Error loading history: {e}")
        return []


def save_content_history(history):
    """
    Save content history to GitHub Gist
    Keeps only last N posts
    """
    if not GIST_ID or not GITHUB_TOKEN:
        print("⚠️ GIST_ID or GITHUB_TOKEN not set - cannot save history")
        return False
    
    try:
        # Trim to last N posts
        history = history[-HISTORY_LIMIT:]
        
        print(f"📤 Saving history to GitHub Gist ({len(history)} posts)...")
        
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Update gist with new history
        payload = {
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps(history, indent=2)
                }
            }
        }
        
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ History saved to gist")
            return True
        else:
            print(f"⚠️ Failed to save gist: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Network error saving history: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error saving history: {e}")
        return False


def add_to_history(content_type):
    """
    Add a new content type to history
    Convenience function that loads, appends, and saves
    """
    history = get_content_history()
    history.append(content_type)
    save_content_history(history)
    return history


def get_recent_types(limit=10):
    """
    Get the most recent N content types
    """
    history = get_content_history()
    return history[-limit:] if history else []


def create_gist():
    """
    Helper function to create a new gist for content history
    Run this once to set up the gist, then use the returned ID
    """
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set")
        return None
    
    try:
        print("🆕 Creating new GitHub Gist for content history...")
        
        url = "https://api.github.com/gists"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "description": "Aesthetic Vibes - Content History Tracker",
            "public": False,  # Private gist
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps([], indent=2)
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
            print(f"   CONTENT_HISTORY_GIST_ID={gist_id}")
            
            return gist_id
        else:
            print(f"❌ Failed to create gist: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating gist: {e}")
        return None


if __name__ == "__main__":
    print("\n🧪 Testing GitHub Gist Storage\n")
    
    # Check if gist exists
    if not GIST_ID:
        print("❌ CONTENT_HISTORY_GIST_ID not set")
        print("\nTo create a new gist, set GITHUB_TOKEN and run:")
        print("  python gist_storage.py --create")
    else:
        print(f"📋 Using Gist ID: {GIST_ID}")
        
        # Test read
        print("\n1️⃣ Testing READ:")
        history = get_content_history()
        print(f"Current history: {history}")
        
        # Test write
        print("\n2️⃣ Testing WRITE:")
        test_history = history + ["TEST_TYPE"]
        success = save_content_history(test_history)
        
        if success:
            print("\n3️⃣ Verifying:")
            new_history = get_content_history()
            print(f"Updated history: {new_history}")
            
            # Clean up test
            if "TEST_TYPE" in new_history:
                new_history.remove("TEST_TYPE")
                save_content_history(new_history)
                print("✅ Test cleanup complete")
        
    print("\n✅ Test complete")

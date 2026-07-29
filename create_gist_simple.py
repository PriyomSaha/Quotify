#!/usr/bin/env python3
"""
Create GitHub Gist without requests library (uses urllib - built-in)
"""

import json
import urllib.request
import urllib.error
import sys

def create_gist(token):
    """Create a private gist for content history"""
    
    url = "https://api.github.com/gists"
    
    payload = {
        "description": "Aesthetic Vibes - Content History Tracker",
        "public": False,
        "files": {
            "content_history.json": {
                "content": "[]"
            }
        }
    }
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        print("🔄 Creating GitHub Gist...")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            gist_id = result['id']
            gist_url = result['html_url']
            
            print("\n" + "="*70)
            print("✅ GIST CREATED SUCCESSFULLY!")
            print("="*70)
            print(f"\n📋 GIST ID: {gist_id}")
            print(f"🔗 URL: {gist_url}")
            print(f"\n⚠️  SAVE THESE - Add to your secrets:")
            print(f"\nGitHub Actions Secret:")
            print(f"  Name: CONTENT_HISTORY_GIST_ID")
            print(f"  Value: {gist_id}")
            print(f"\nRender Environment Variables:")
            print(f"  CONTENT_HISTORY_GIST_ID = {gist_id}")
            print(f"  GITHUB_TOKEN = {token[:10]}...{token[-4:]}")
            print("\n" + "="*70)
            
            return gist_id
            
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"\n❌ Failed to create gist: {e.code}")
        print(f"Response: {error_msg}")
        
        if e.code == 401:
            print("\n⚠️  Authentication failed - check your token:")
            print("  1. Go to: https://github.com/settings/tokens")
            print("  2. Make sure 'gist' scope is checked")
            print("  3. Token should start with 'ghp_' or 'github_pat_'")
        
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "="*70)
    print("CREATE GITHUB GIST FOR CONTENT HISTORY")
    print("="*70 + "\n")
    
    # Try to load from .env file first
    import os
    token = None
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv('GITHUB_TOKEN')
        if token:
            print("✅ Loaded GITHUB_TOKEN from .env file")
        else:
            print("⚠️ GITHUB_TOKEN not found in .env")
    except ImportError:
        print("⚠️ python-dotenv not installed, trying command line...")
    
    # Fallback to command line argument
    if not token and len(sys.argv) >= 2:
        token = sys.argv[1]
        print("✅ Using token from command line")
    
    if not token:
        print("\n❌ No GitHub token provided!")
        print("\nOption 1: Add to .env file")
        print("  GITHUB_TOKEN=your_token_here")
        print("\nOption 2: Pass as argument")
        print("  python3 create_gist_simple.py YOUR_GITHUB_TOKEN")
        print("\nGet token from: https://github.com/settings/tokens")
        print("Required scope: ✅ gist")
        sys.exit(1)
    
    if not token.startswith(('ghp_', 'github_pat_', 'gho_')):
        print("⚠️  Warning: Token format looks incorrect")
        print("   GitHub tokens usually start with 'ghp_', 'github_pat_', or 'gho_'")
        print("   Trying anyway...\n")
    
    gist_id = create_gist(token)
    
    if gist_id:
        print("\n✅ Setup complete! Next steps:")
        print("  1. Add CONTENT_HISTORY_GIST_ID to GitHub Secrets")
        print("  2. Add both variables to Render Environment")
        print("  3. Commit and push your code")
    else:
        print("\n❌ Setup failed - please check the error above")

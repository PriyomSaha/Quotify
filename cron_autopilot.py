#!/usr/bin/env python3
"""
Direct cron job script - no API needed
Run this directly from Render Cron Job
"""

from QuoteGeneration import generate_quote
from ImageGeneration import create_neon_quote_image
from FBUpload import schedule_photo_after, post_to_instagram_from_fb_url
from check_last_post import should_publish_new_post

def main():
    try:
        print("🚀 Autopilot started")
        
        # Check if enough time has passed since last post (2 hours minimum)
        if not should_publish_new_post(min_hours=2):
            print("⏭️ Skipping - posted too recently")
            return
        
        # Generate quote
        quote = generate_quote()
        if not quote or not quote.strip():
            print("❌ Quote failed")
            return
        
        with open("generated_quote.txt", "w", encoding="utf-8") as f:
            f.write(quote)
        print(f"✅ Quote: {quote[:50]}...")
        
        # Create image
        create_neon_quote_image(quote, "template.jpg", "image.jpg")
        print("✅ Image created")
        
        # Upload to Facebook
        fb_url = schedule_photo_after("image.jpg", "", 0, 0)
        if not fb_url:
            print("❌ FB failed")
            return
        print("✅ FB uploaded")
        
        # Post to Instagram
        ig_result = post_to_instagram_from_fb_url(fb_url, "")
        ig_post_id = ig_result.get("id", "")
        
        if not ig_post_id:
            print("⚠️ IG failed (FB ok)")
            return
        
        print(f"✅ IG: {ig_post_id}")
        print("🎉 Done!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

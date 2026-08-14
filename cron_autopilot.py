#!/usr/bin/env python3
"""
Direct cron job script - no API needed
Run this directly from Render Cron Job
"""

import argparse

from QuoteGeneration import generate_quote
from ImageGeneration import create_neon_quote_image
from FBUpload import schedule_photo_after, post_to_instagram_from_fb_url
from check_last_post import should_publish_new_post
from event_detector import build_quote_caption, get_today_event

def main(no_upload=False, skip_recent_check=False, output_path="image.jpg"):
    try:
        print("🚀 Autopilot started")

        event = get_today_event()
        if event:
            print(f"🎉 Event mode for quote flow: {event.get('name')}")
        else:
            print("ℹ️ No event active. Using normal random quote flow.")
        
        # Check if enough time has passed since last post (2 hours minimum)
        if not skip_recent_check and not should_publish_new_post(min_hours=2):
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
        create_neon_quote_image(quote, "template.jpg", output_path)
        print(f"✅ Image created: {output_path}")

        if no_upload:
            print("✅ Quote test flow completed without upload")
            return
        
        # Upload to Facebook
        caption = build_quote_caption(event)
        if caption:
            print(f"Caption preview: {caption[:200]}")

        fb_url = schedule_photo_after(output_path, caption, 0, 0)
        if not fb_url:
            print("❌ FB failed")
            return
        print("✅ FB uploaded")
        
        # Post to Instagram
        ig_result = post_to_instagram_from_fb_url(fb_url, caption)
        ig_post_id = ig_result.get("id", "")
        
        if not ig_post_id:
            print("⚠️ IG failed (FB ok)")
            return
        
        print(f"✅ IG: {ig_post_id}")
        print("🎉 Done!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run direct quote cron flow. Use EVENT_TEST_DATE in .env for event-date testing.")
    parser.add_argument("--no-upload", action="store_true", help="Generate quote image only; do not upload")
    parser.add_argument("--skip-recent-check", action="store_true", help="Skip last-post timing check for local tests")
    parser.add_argument("--output", default="image.jpg", help="Output image path")
    args = parser.parse_args()

    main(
        no_upload=args.no_upload,
        skip_recent_check=args.skip_recent_check,
        output_path=args.output,
    )

import argparse
import os
import time
from dotenv import load_dotenv
from QuoteGeneration import generate_quote, build_quote_post_caption
from ImageGeneration import create_neon_quote_image
from FBUpload import schedule_photo_after, post_to_instagram_from_fb_url
from event_detector import CONTENT_QUOTE, get_today_event

load_dotenv()


def get_bool_env(name, default=False):
    """Read a boolean environment variable from .env / environment."""
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main(no_upload=None, output_path="image.jpg"):
    """
    Main runner that orchestrates the entire quote-to-social-media pipeline.
    Generates a quote → Creates neon image → Uploads to Facebook → Posts to Instagram.
    """
    
    try:
        if no_upload is None:
            no_upload = get_bool_env("NO_UPLOAD_QUOTES", default=False)

        print(f"📤 Quote upload enabled: {not no_upload}")

        event = get_today_event(content_type=CONTENT_QUOTE)
        if event:
            print(f"🎉 Event mode for quote flow: {event.get('name')}")
        else:
            print("ℹ️ No event active. Using normal random quote flow.")

        # -------------------------------------------------
        # Step 1: Generate Quote
        # -------------------------------------------------
        print("📝 Step 1: Generating quote...")
        quote_input = generate_quote()
        
        if not quote_input or not quote_input.strip():
            raise Exception("Quote generation failed: returned empty text")
        
        print(f"✅ Quote generated successfully")
        print(f"   Quote: {quote_input[:50]}..." if len(quote_input) > 50 else f"   Quote: {quote_input}")
        
        # -------------------------------------------------
        # Step 2: Create Neon Quote Image
        # -------------------------------------------------
        print("\n🎨 Step 2: Creating neon quote image...")
        create_neon_quote_image(
            raw_text=quote_input,
            template_path="template.jpg",
            output_path=output_path,
        )
        print(f"✅ Image created successfully: {output_path}")

        if no_upload:
            print("\n✅ Quote test flow completed without upload")
            print(f"🖼️ Image: {output_path}")
            return
        
        # -------------------------------------------------
        # Step 3: Wait 10 seconds
        # -------------------------------------------------
        print("\n⏳ Step 3: Waiting 10 seconds before upload...")
        time.sleep(10)
        print("✅ Wait complete")
        
        # -------------------------------------------------
        # Step 4: Upload to Facebook and get CDN URL
        # -------------------------------------------------
        print("\n📤 Step 4: Uploading image to Facebook...")
        caption = build_quote_post_caption(quote_input, event)
        if caption:
            print(f"Caption preview: {caption[:200]}")

        fb_cdn_url = schedule_photo_after(
            image_path=output_path,
            caption=caption,
            minutes=0,
            hours=0
        )
        
        if not fb_cdn_url:
            raise Exception("Facebook upload failed: no CDN URL returned")
        
        print(f"✅ Facebook upload successful")
        print(f"   CDN URL: {fb_cdn_url}")
        
        # -------------------------------------------------
        # Step 5: Post to Instagram using Facebook CDN URL
        # -------------------------------------------------
        print("\n📱 Step 5: Publishing to Instagram...")
        ig_result = post_to_instagram_from_fb_url(
            fb_image_url=fb_cdn_url,
            caption=caption
        )
        
        ig_post_id = ig_result.get("id")
        if not ig_post_id:
            raise Exception(f"Instagram publish failed: {ig_result}")
        
        print(f"✅ Instagram post published successfully")
        print(f"   Post ID: {ig_post_id}")
        
        # -------------------------------------------------
        # Final Success Message
        # -------------------------------------------------
        print("\n" + "="*50)
        print("🎉 All steps completed successfully!")
        print("="*50)
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: File not found - {e}")
        print("   Make sure template.jpg exists in the project root.")
        exit(1)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("   Process stopped.")
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run quote flow. Use EVENT_TEST_DATE and NO_UPLOAD_QUOTES in .env for local testing.")
    parser.add_argument("--output", default="image.jpg", help="Output image path")
    args = parser.parse_args()

    main(
        output_path=args.output,
    )

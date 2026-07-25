import time
from QuoteGeneration import generate_quote
from ImageGeneration import create_neon_quote_image
from FBUpload import schedule_photo_after, post_to_instagram_from_fb_url


def main():
    """
    Main runner that orchestrates the entire quote-to-social-media pipeline.
    Generates a quote → Creates neon image → Uploads to Facebook → Posts to Instagram.
    """
    
    try:
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
            output_path="image.jpg",
        )
        print("✅ Image created successfully: image.jpg")
        
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
        fb_cdn_url = schedule_photo_after(
            image_path="image.jpg",
            caption="",  # Blank caption as specified
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
            caption=""  # Blank caption as specified
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
    main() # main call

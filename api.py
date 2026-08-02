from fastapi import FastAPI, BackgroundTasks, HTTPException
import os
import sys
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from QuoteGeneration import generate_quote
from ImageGeneration import create_neon_quote_image
from FBUpload import schedule_photo_after, post_to_instagram_from_fb_url

# -------------------------------------------------
# Logging Configuration
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# FastAPI App Initialization
# -------------------------------------------------
app = FastAPI(
    title="Quote to Social Media API",
    description="Minimal API for Render health checks and autopilot",
    version="2.0.0"
)

# -------------------------------------------------
# Background Task Function
# -------------------------------------------------
def execute_full_pipeline(caption: str, template_path: str, output_path: str):
    """
    Executes the full pipeline in the background.
    This runs asynchronously after the endpoint returns.
    Detailed logging for debugging and monitoring.
    """
    steps = {
        "quote_generated": False,
        "image_created": False,
        "facebook_uploaded": False,
        "instagram_published": False
    }
    
    quote_text = ""
    fb_cdn_url = ""
    ig_post_id = ""
    
    try:
        logger.info("🚀 Pipeline started - Executing full autopilot")
        logger.info(f"Parameters: caption='{caption}', template='{template_path}', output='{output_path}'")
        
        # Step 1: Generate Quote
        logger.info("📝 Step 1/4: Generating AI quote...")
        try:
            quote_text = generate_quote()
            
            if not quote_text or not quote_text.strip():
                logger.error("❌ Quote generation returned empty text")
                logger.error(f"Quote value: '{quote_text}'")
                return
            
            with open("generated_quote.txt", "w", encoding="utf-8") as f:
                f.write(quote_text)
            
            steps["quote_generated"] = True
            logger.info(f"✅ Quote generated successfully: {quote_text[:100]}...")
            logger.info(f"Quote length: {len(quote_text)} characters")
            
        except Exception as e:
            logger.error(f"❌ Exception in quote generation: {type(e).__name__}: {str(e)}")
            raise
        
        # Step 2: Create Image
        logger.info(f"🎨 Step 2/4: Creating neon image from quote...")
        try:
            if not os.path.exists(template_path):
                logger.error(f"❌ Template file not found at: {template_path}")
                logger.error(f"Current working directory: {os.getcwd()}")
                logger.error(f"Files in directory: {os.listdir('.')}")
                return
            
            logger.info(f"Template found: {template_path} ({os.path.getsize(template_path)} bytes)")
            
            create_neon_quote_image(
                raw_text=quote_text,
                template_path=template_path,
                output_path=output_path
            )
            
            if not os.path.exists(output_path):
                logger.error(f"❌ Image file not created at: {output_path}")
                return
            
            steps["image_created"] = True
            logger.info(f"✅ Image created successfully: {output_path} ({os.path.getsize(output_path)} bytes)")
            
        except Exception as e:
            logger.error(f"❌ Exception in image creation: {type(e).__name__}: {str(e)}")
            raise
        
        # Step 3: Upload to Facebook
        logger.info("📤 Step 3/4: Uploading to Facebook...")
        try:
            fb_cdn_url = schedule_photo_after(
                image_path=output_path,
                caption=caption,
                hours=0,
                minutes=0
            )
            
            if not fb_cdn_url:
                logger.error("❌ Facebook upload returned no CDN URL")
                return
            
            steps["facebook_uploaded"] = True
            logger.info(f"✅ Facebook upload successful")
            logger.info(f"CDN URL: {fb_cdn_url[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ Exception in Facebook upload: {type(e).__name__}: {str(e)}")
            raise
        
        # Step 4: Publish to Instagram
        logger.info("📱 Step 4/4: Publishing to Instagram...")
        try:
            ig_result = post_to_instagram_from_fb_url(
                fb_image_url=fb_cdn_url,
                caption=caption
            )
            
            logger.info(f"Instagram API response: {ig_result}")
            
            ig_post_id = ig_result.get("id", "")
            
            if not ig_post_id:
                logger.warning("⚠️ Instagram publish failed - no post ID returned")
                logger.warning(f"Full IG response: {ig_result}")
                logger.info("Note: Facebook upload succeeded, check FB manually")
                return
            
            steps["instagram_published"] = True
            logger.info(f"✅ Instagram post published successfully")
            logger.info(f"Instagram Post ID: {ig_post_id}")
            logger.info("🎉 Full pipeline completed successfully!")
            logger.info(f"Final steps status: {steps}")
            
        except Exception as e:
            logger.error(f"❌ Exception in Instagram publish: {type(e).__name__}: {str(e)}")
            logger.info(f"Note: Facebook upload succeeded (URL: {fb_cdn_url[:50]}...)")
            raise
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed with exception: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        logger.error(f"Steps completed before failure: {steps}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")

# -------------------------------------------------
# Endpoint: Autopilot - Full Pipeline
# -------------------------------------------------
@app.get("/autopilot")
async def full_pipeline_autopilot(
    background_tasks: BackgroundTasks,
    caption: str = "",
    template_path: str = "template.jpg",
    output_path: str = "image.jpg"
):
    """
    🚀 FULL AUTOMATED PIPELINE - Perfect for cron jobs!
    
    Returns IMMEDIATELY (prevents cron timeout), then processes in background.
    
    Does everything in one call:
    1. Generates AI quote
    2. Creates neon image
    3. Uploads to Facebook
    4. Publishes to Instagram
    
    Just hit this URL with a cron job and you're done!
    
    Query Parameters:
        caption: Photo caption for both platforms (default: empty)
        template_path: Path to template image (default: template.jpg)
        output_path: Path for output image (default: image.jpg)
        
    Returns:
        Immediate acknowledgment (background processing starts)
    """
    logger.info("⚡ /autopilot endpoint called")
    logger.info(f"Request params: caption='{caption}', template='{template_path}', output='{output_path}'")
    
    # Verify template exists before queuing
    if not os.path.exists(template_path):
        logger.error(f"❌ Template file not found: {template_path}")
        return {
            "status": "error",
            "message": f"Template file not found: {template_path}"
        }
    
    # Add the pipeline execution to background tasks
    background_tasks.add_task(
        execute_full_pipeline,
        caption=caption,
        template_path=template_path,
        output_path=output_path
    )
    
    logger.info("✅ Background task queued successfully")
    
    # Return immediately with minimal response for cron jobs
    return {"status": "ok", "message": "Pipeline started in background"}

# -------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running and dependencies are accessible.
    """
    logger.info("🔍 Health check requested")
    
    health_status = {
        "status": "healthy",
        "api_version": "2.0.0",
        "checks": {}
    }
    
    # Check if template file exists
    template_exists = os.path.exists("template.jpg")
    health_status["checks"]["template_file"] = "ok" if template_exists else "missing"
    
    if not template_exists:
        logger.warning("⚠️ Template file (template.jpg) not found during health check")
        health_status["status"] = "degraded"
    
    # Check environment variables
    required_env_vars = ["GEMINI_API_KEY", "PAGE_ID", "PAGE_ACCESS_TOKEN", "API_VERSION", "IG_USER_ID"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        health_status["checks"]["environment_variables"] = f"missing: {', '.join(missing_vars)}"
        health_status["status"] = "unhealthy"
        logger.error(f"❌ Missing environment variables: {missing_vars}")
    else:
        health_status["checks"]["environment_variables"] = "ok"
    
    logger.info(f"Health check result: {health_status['status']}")
    
    return health_status



# -------------------------------------------------
# Background Task: Generate Complete Reel
# -------------------------------------------------
def execute_reel_generation():
    """
    Generates a complete reel: story → images → voice → video → upload to FB/IG.
    Uses the SAME upload pattern as /autopilot endpoint.
    """
    try:
        from Reels.story_generation import generate_story
        from Reels.image_generation import generate_images_for_reel
        from Reels.voice_generation import generate_voice
        from Reels.video_generation import create_reel
        import json
        import time
        import requests
        
        logger.info("🎬 Starting Reel Generation Pipeline")
        
        # Create timestamped output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("Reels/output") / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Output folder: {output_dir}")
        
        # Step 1: Generate Story
        logger.info("📝 Step 1/5: Generating story...")
        story = generate_story()
        
        story_file = output_dir / "story.json"
        with open(story_file, "w", encoding="utf-8") as f:
            json.dump(story, f, indent=4, ensure_ascii=False)
        
        logger.info(f"✅ Story: {story.get('quote', '')[:50]}...")
        
        # Step 2: Generate Images
        logger.info("🎨 Step 2/5: Generating images...")
        image_dir = output_dir / "images"
        images = generate_images_for_reel(
            reel_json=story,
            output_dir=image_dir,
            prefix="scene"
        )
        logger.info(f"✅ Generated {len(images)} images")
        
        # Step 3: Generate Voice
        logger.info("🎤 Step 3/5: Generating voiceover...")
        audio_path = output_dir / "voiceover.mp3"
        generate_voice(
            text=story["narration"],
            output_file=str(audio_path)
        )
        logger.info(f"✅ Voiceover generated")
        
        # Step 4: Compose Video
        logger.info("🎬 Step 4/5: Composing video...")
        video_file = output_dir / "reel.mp4"
        create_reel(
            images=images,
            narration_audio=str(audio_path),
            output_file=str(video_file)
        )
        logger.info(f"✅ Video created: {video_file}")
        
        # Step 5: Upload to FB and Instagram (SAME PATTERN AS /autopilot)
        logger.info("📤 Step 5/5: Uploading to social media...")
        
        caption = story.get("quote", "")[:2000]
        
        # Upload video to Facebook
        logger.info("Uploading video to Facebook...")
        PAGE_ID = os.getenv("PAGE_ID")
        PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
        API_VERSION = os.getenv("API_VERSION", "v21.0")
        
        fb_url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/videos"
        
        with open(str(video_file), "rb") as video:
            fb_response = requests.post(
                fb_url,
                files={"source": video},
                data={
                    "description": caption,
                    "published": "true",
                    "access_token": PAGE_ACCESS_TOKEN,
                },
                timeout=300
            )
        
        fb_result = fb_response.json()
        fb_video_id = fb_result.get("id")
        
        if not fb_video_id:
            logger.error(f"❌ Facebook upload failed: {fb_result}")
            return
        
        logger.info(f"✅ Facebook video uploaded: {fb_video_id}")
        
        # Get video URL from Facebook
        video_info_url = f"https://graph.facebook.com/{API_VERSION}/{fb_video_id}"
        video_info_res = requests.get(
            video_info_url,
            params={"fields": "source", "access_token": PAGE_ACCESS_TOKEN},
        )
        
        fb_video_url = video_info_res.json().get("source", "")
        
        if not fb_video_url:
            logger.warning("⚠️ Could not retrieve FB video URL")
            return
        
        logger.info(f"✅ FB Video URL: {fb_video_url[:50]}...")
        
        # Post to Instagram as REEL
        logger.info("Publishing to Instagram as Reel...")
        IG_USER_ID = os.getenv("IG_USER_ID")
        
        # Create media container for REEL
        container_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media"
        container_res = requests.post(
            container_url,
            data={
                "video_url": fb_video_url,
                "caption": caption,
                "media_type": "REELS",
                "access_token": PAGE_ACCESS_TOKEN,
            },
        ).json()
        
        creation_id = container_res.get("id")
        
        if not creation_id:
            logger.error(f"❌ IG Container creation failed: {container_res}")
            return
        
        logger.info(f"✅ IG Container created: {creation_id}")
        
        # Wait for Instagram to process the video
        logger.info("⏳ Waiting for Instagram to process video...")
        time.sleep(15)
        
        # Publish the reel
        publish_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media_publish"
        publish_res = requests.post(
            publish_url,
            data={
                "creation_id": creation_id,
                "access_token": PAGE_ACCESS_TOKEN,
            },
        ).json()
        
        ig_post_id = publish_res.get("id", "")
        
        if ig_post_id:
            logger.info(f"✅ Instagram Reel published: {ig_post_id}")
        else:
            logger.warning(f"⚠️ Instagram publish failed: {publish_res}")
        
        logger.info("🎉 Reel generation pipeline completed!")
        logger.info(f"📁 Output: {output_dir}")
        logger.info(f"🎬 Video: {video_file}")
        logger.info(f"📱 Instagram: {ig_post_id}")
        
        # Delete the entire output folder after successful upload
        logger.info(f"🗑️ Deleting output folder: {output_dir}")
        shutil.rmtree(output_dir)
        logger.info("✅ Output folder deleted successfully")
        
    except Exception as e:
        logger.error(f"❌ Reel generation failed: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")

# -------------------------------------------------
# Endpoint: Generate Reel
# -------------------------------------------------
@app.get("/generate-reel")
async def generate_reel_endpoint(background_tasks: BackgroundTasks):
    """
    🎬 GENERATE COMPLETE REEL AND UPLOAD TO FB/INSTAGRAM
    
    Same pattern as /autopilot but for video reels!
    
    Just hit this endpoint and it will:
    1. Generate AI story
    2. Create cinematic images
    3. Generate voiceover
    4. Compose video with subtitles
    5. Upload to Facebook and Instagram as REEL
    6. Delete all temporary files after upload
    
    Returns immediately, processes in background.
    
    Example:
        GET https://your-app.onrender.com/generate-reel
    
    Returns:
        {"status": "ok", "message": "Reel generation started"}
    """
    logger.info("⚡ /generate-reel endpoint called")
    
    # Verify required environment variables
    required_vars = [
        "GEMINI_API_KEY",
        "CF_ACCOUNT_ID_1", 
        "CF_TOKEN_1",
        "PAGE_ID",
        "PAGE_ACCESS_TOKEN",
        "IG_USER_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        return {
            "status": "error",
            "message": f"Missing required env vars: {', '.join(missing_vars)}"
        }
    
    # Add the reel generation to background tasks
    background_tasks.add_task(execute_reel_generation)
    
    logger.info("✅ Reel generation task queued")
    
    # Return immediately (same pattern as /autopilot)
    return {
        "status": "ok",
        "message": "Reel generation started in background (takes 3-5 minutes)"
    }

# -------------------------------------------------
# Run the API
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment variable for Render compatibility
    port = int(os.environ.get("PORT", 8000))
    # Set timeout to 10 minutes (600 seconds) for video processing
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=600, log_level="warning")

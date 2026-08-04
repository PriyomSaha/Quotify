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
    ],
    force=True
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
# Startup Event: Pre-load Vosk Model
# -------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    Pre-load Vosk model at startup to avoid delays on first request.
    Uses 'small-en-us' model (~40MB) which fits in Render's 512MB RAM.
    """
    logger.info("🚀 API Starting up...")
    logger.info("📦 Skipping Vosk pre-load (will load on first request)...")
    
    # Temporarily disabled for local testing - model will load on first reel generation
    # try:
    #     from Reels.subtitle_generation_vosk import _get_model
    #     _get_model()  # This will load and cache the Vosk model
    #     logger.info("✅ Vosk model pre-loaded successfully")
    # except Exception as e:
    #     logger.warning(f"⚠️ Could not pre-load Vosk model: {e}")
    #     logger.warning("Model will be loaded on first reel generation request")

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
    Uses the refactored generate_complete_reel() function from Reels.main
    """
    # -------------------------------------------------
    # Initial logging & setup (unchanged)
    # -------------------------------------------------
    logger.info("=" * 50)
    logger.info("🎬 REEL GENERATION STARTED")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 50)
    sys.stdout.flush()

    try:
        # -------------------------------------------------
        # Import reel generation module (unchanged)
        # -------------------------------------------------
        logger.info("📦 Importing reel generation module...")
        from Reels_main import generate_complete_reel
        logger.info("✅ Module imported successfully")
        sys.stdout.flush()

        # -------------------------------------------------
        # Generate the complete reel (unchanged)
        # -------------------------------------------------
        logger.info("🎬 Generating complete reel...")
        sys.stdout.flush()
        result = generate_complete_reel()
        logger.info("✅ Reel generation completed successfully!")
        logger.info(f"📁 Output folder: {result['output_folder']}")
        logger.info(f"🎬 Video file: {result['video_file']}")
        sys.stdout.flush()

        # -------------------------------------------------
        # Prepare paths & caption (unchanged)
        # -------------------------------------------------
        video_file = Path(result["video_file"])
        output_dir = Path(result["output_folder"])
        story = result["story"]
        caption = story.get("title", story.get("narration", "")[:100])[:2000]
        logger.info(f"Caption (first 50 chars): {caption[:50]}...")
        logger.info(f"Caption length: {len(caption)} characters")
        sys.stdout.flush()

        import requests
        import time

        # -------------------------------------------------
        # Cloudinary upload (unchanged)
        # -------------------------------------------------
        cloudinary_url = None
        cloudinary_public_id = None
        delete_video_from_cloudinary = None  # will be set if upload succeeds

        logger.info("📤 Step 5a: Uploading video to Cloudinary...")
        sys.stdout.flush()
        try:
            from Reels.cloudinary_uploader import (
                upload_video_to_cloudinary,
                delete_video_from_cloudinary,
            )

            cloudinary_result = upload_video_to_cloudinary(
                video_path=str(video_file),
                folder="instagram_reels",
                public_id=f"reel_{output_dir.name}",
            )
            cloudinary_url = cloudinary_result["secure_url"]
            cloudinary_public_id = cloudinary_result["public_id"]
            logger.info("✅ Video uploaded to Cloudinary")
            logger.info(f"🔗 Public URL: {cloudinary_url[:80]}...")
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"❌ Cloudinary upload failed: {e}")
            import traceback

            logger.error(traceback.format_exc())
            cloudinary_url = None
            cloudinary_public_id = None
            delete_video_from_cloudinary = None

        # -------------------------------------------------
        # Facebook upload (unchanged)
        # -------------------------------------------------
        logger.info("📤 Step 5b: Uploading video to Facebook...")
        sys.stdout.flush()
        PAGE_ID = os.getenv("PAGE_ID")
        PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
        API_VERSION = os.getenv("API_VERSION", "v21.0")

        logger.info(f"Facebook API Version: {API_VERSION}")
        logger.info(
            f"Page ID: {PAGE_ID[:10]}..." if PAGE_ID else "Page ID: MISSING"
        )
        logger.info(
            f"Video file size: {video_file.stat().st_size / (1024*1024):.2f} MB"
        )
        sys.stdout.flush()

        fb_url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/videos"
        logger.info(f"Facebook upload URL: {fb_url}")
        logger.info("⏳ Uploading video to Facebook (this may take 1-3 minutes)...")
        sys.stdout.flush()

        fb_video_id = None
        try:
            with open(str(video_file), "rb") as video:
                fb_response = requests.post(
                    fb_url,
                    files={"source": video},
                    data={
                        "description": caption,
                        "published": "true",
                        "access_token": PAGE_ACCESS_TOKEN,
                    },
                    timeout=300,
                )
                logger.info("✅ Facebook upload request completed")
                logger.info(f"Response status code: {fb_response.status_code}")
                sys.stdout.flush()

                fb_result = fb_response.json()
                logger.info(f"Facebook response: {fb_result}")
                sys.stdout.flush()
                fb_video_id = fb_result.get("id")
                if fb_video_id:
                    logger.info(f"✅ Facebook video uploaded: {fb_video_id}")
                    sys.stdout.flush()
                else:
                    logger.error(f"❌ Facebook upload failed: {fb_result}")
                    sys.stdout.flush()
        except Exception as upload_error:
            logger.error(f"❌ Facebook upload request failed: {upload_error}")
            import traceback

            logger.error(traceback.format_exc())
        creation_id = None
        # -------------------------------------------------
        # Instagram Reel creation (modified)
        # -------------------------------------------------
        if not cloudinary_url:
            logger.error("❌ Cannot post to Instagram without Cloudinary URL")
            logger.warning("⚠️ Facebook upload completed, but Instagram post skipped")
            sys.stdout.flush()
            # Skip Instagram posting if no Cloudinary URL
        else:
            logger.info("📱 Step 5c: Publishing to Instagram as Reel...")
            sys.stdout.flush()

            IG_USER_ID = os.getenv("IG_USER_ID")
            logger.info(
                f"Instagram User ID: {IG_USER_ID[:10]}..."
                if IG_USER_ID
                else "IG User ID: MISSING"
            )
            sys.stdout.flush()

            # Create media container for REEL (using Cloudinary URL)
            logger.info("Creating Instagram media container with Cloudinary URL...")
            sys.stdout.flush()

            container_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media"
            container_res = requests.post(
                container_url,
                data={
                    "video_url": cloudinary_url,
                    "caption": caption,
                    "media_type": "REELS",
                    "access_token": PAGE_ACCESS_TOKEN,
                },
            ).json()

            creation_id = container_res.get("id")
            logger.info(f"Container response: {container_res}")
            sys.stdout.flush()

            # ---------- Modified block ----------
            # Abort if we didn't get a valid creation_id
            if not creation_id:
                logger.error(f"❌ IG Container creation failed: {container_res}")
                error_message = container_res.get("error", {}).get(
                    "message", "Unknown error"
                )
                logger.error(f"Error details: {error_message}")
                sys.stdout.flush()
                return            # <‑‑ stop further processing
            else:
                logger.info(f"✅ IG Container created: {creation_id}")
                sys.stdout.flush()
            # -----------------------------------

        # -------------------------------------------------
        # Poll container status (unchanged)
        # -------------------------------------------------
        logger.info("⏳ Polling container status (this can take 30-90 seconds)...")
        sys.stdout.flush()
        max_attempts = 30
        attempt = 0
        container_ready = False
        status_code = "UNKNOWN"

        while attempt < max_attempts:
            attempt += 1
            time.sleep(3)

            status_url = f"https://graph.facebook.com/{API_VERSION}/{creation_id}"
            status_res = requests.get(
                status_url,
                params={
                    "fields": "status_code",
                    "access_token": PAGE_ACCESS_TOKEN,
                },
            )
            status_data = status_res.json()
            status_code = status_data.get("status_code", "UNKNOWN")
            logger.info(f"Attempt {attempt}/{max_attempts}: Status = {status_code}")
            sys.stdout.flush()

            if status_code == "FINISHED":
                container_ready = True
                logger.info("✅ Container ready for publishing!")
                sys.stdout.flush()
                break
            elif status_code == "ERROR":
                logger.error(f"❌ Container processing failed: {status_data}")
                sys.stdout.flush()
                return
            elif status_code in ["EXPIRED", "PUBLISHED"]:
                logger.error(f"❌ Container status invalid: {status_code}")
                sys.stdout.flush()
                return

        if not container_ready:
            logger.error(
                f"❌ Container not ready after {max_attempts * 3} seconds"
            )
            logger.error(f"Final status: {status_code}")
            sys.stdout.flush()
            return

        # -------------------------------------------------
        # Publish the reel (unchanged)
        # -------------------------------------------------
        logger.info("Publishing Instagram Reel...")
        sys.stdout.flush()
        publish_url = f"https://graph.facebook.com/{API_VERSION}/{IG_USER_ID}/media_publish"
        publish_res = requests.post(
            publish_url,
            data={
                "creation_id": creation_id,
                "access_token": PAGE_ACCESS_TOKEN,
            },
        ).json()
        ig_post_id = publish_res.get("id", "")
        logger.info(f"Publish response: {publish_res}")
        sys.stdout.flush()

        if ig_post_id:
            logger.info(f"✅ Instagram Reel published: {ig_post_id}")

            # ----------- Modified block -----------
            # Safe deletion of Cloudinary video
            if cloudinary_public_id:
                logger.info("🗑️ Deleting video from Cloudinary...")
                try:
                    # Ensure the delete helper is available
                    if delete_video_from_cloudinary:
                        delete_video_from_cloudinary(cloudinary_public_id)
                        logger.info(
                            "✅ Cloudinary video deleted successfully"
                        )
                    else:
                        logger.warning(
                            "⚠️ Cloudinary delete function not available, skipping deletion"
                        )
                except Exception as delete_error:
                    logger.warning(
                        f"⚠️ Failed to delete from Cloudinary: {delete_error}"
                    )
                    # Continue even if deletion fails
                sys.stdout.flush()
            # -------------------------------------

        else:
            logger.warning(f"⚠️ Instagram publish failed: {publish_res}")
            if cloudinary_public_id:
                logger.info("📁 Video kept in Cloudinary for debugging")

        sys.stdout.flush()
        logger.info("🎉 Reel generation pipeline completed!")
        sys.stdout.flush()
        logger.info(f"📁 Output: {output_dir}")
        logger.info(f"🎬 Video: {video_file}")
        logger.info(
            f"📦 Facebook: {fb_video_id if fb_video_id else 'N/A'}"
        )
        logger.info(
            f"📱 Instagram: {ig_post_id if ig_post_id else 'N/A'}"
        )

        # -------------------------------------------------
        # Clean‑up temporary folder (unchanged)
        # -------------------------------------------------
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
# Endpoint: Serve Reel Videos
# -------------------------------------------------
from fastapi.responses import FileResponse

@app.get("/reels/{timestamp}/reel.mp4")
async def serve_reel_video(timestamp: str):
    """
    Serve reel video file for Instagram upload.
    
    Instagram requires a publicly accessible URL to upload reels.
    This endpoint serves the generated reel.mp4 file.
    
    Args:
        timestamp: Folder timestamp (e.g., "20260803_153500")
        
    Returns:
        MP4 video file
        
    Raises:
        404: If video file doesn't exist
    """
    video_path = Path(f"Reels/output/{timestamp}/reel.mp4")
    
    if not video_path.exists():
        logger.warning(f"⚠️ Video not found: {video_path}")
        raise HTTPException(status_code=404, detail=f"Video not found: {timestamp}")
    
    logger.info(f"📹 Serving reel video: {timestamp}")
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename="reel.mp4"
    )

# -------------------------------------------------
# Run the API
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment variable for Render compatibility
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting API on port {port}")
    # Set timeout to 10 minutes (600 seconds) for video processing
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=600, log_level="info")

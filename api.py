from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import asyncio
from datetime import datetime
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
    description="API endpoints for generating quotes, creating images, and posting to Facebook/Instagram",
    version="1.0.0"
)

# -------------------------------------------------
# Request/Response Models
# -------------------------------------------------
class QuoteResponse(BaseModel):
    """Response model for quote generation"""
    quote: str
    success: bool
    message: str

class ImageRequest(BaseModel):
    """Request model for image generation"""
    quote_text: Optional[str] = None  # Optional: if not provided, reads from generated_quote.txt
    quote_file: str = "generated_quote.txt"  # File to read quote from if quote_text not provided
    template_path: str = "template.jpg"
    output_path: str = "image.jpg"

class ImageResponse(BaseModel):
    """Response model for image generation"""
    output_path: str
    success: bool
    message: str

class FBUploadRequest(BaseModel):
    """Request model for Facebook upload"""
    image_path: str
    caption: str = ""
    hours: int = 0
    minutes: int = 0

class FBUploadResponse(BaseModel):
    """Response model for Facebook upload"""
    fb_cdn_url: str
    success: bool
    message: str

class IGUploadRequest(BaseModel):
    """Request model for Instagram upload"""
    fb_image_url: str
    caption: str = ""

class IGUploadResponse(BaseModel):
    """Response model for Instagram upload"""
    post_id: str
    success: bool
    message: str

class FullPipelineResponse(BaseModel):
    """Response model for full pipeline execution"""
    quote: str
    image_path: str
    fb_cdn_url: str
    ig_post_id: str
    success: bool
    message: str
    steps_completed: dict

class SocialMediaUploadRequest(BaseModel):
    """Request model for combined Facebook + Instagram upload"""
    image_path: str = "image.jpg"
    caption: str = ""
    hours: int = 0
    minutes: int = 0

class SocialMediaUploadResponse(BaseModel):
    """Response model for combined Facebook + Instagram upload"""
    fb_cdn_url: str
    ig_post_id: str
    success: bool
    message: str
    fb_status: str
    ig_status: str

# -------------------------------------------------
# Endpoint: Generate Quote
# -------------------------------------------------
@app.get("/generatequote", response_model=QuoteResponse)
async def generate_quote_endpoint():
    """
    Generates a motivational quote using AI and stores it in generated_quote.txt.
    Maximum wait time: 2 minutes.
    
    Returns:
        QuoteResponse: Contains the generated quote text
    """
    try:
        print("📝 Generating quote...")
        quote_text = generate_quote()
        
        if not quote_text or not quote_text.strip():
            raise HTTPException(
                status_code=500,
                detail="Quote generation failed: returned empty text"
            )
        
        # Save quote to file for later use
        with open("generated_quote.txt", "w", encoding="utf-8") as f:
            f.write(quote_text)
        
        print(f"✅ Quote generated and saved: {quote_text[:50]}...")
        return QuoteResponse(
            quote=quote_text,
            success=True,
            message="Quote generated and saved to generated_quote.txt"
        )
        
    except Exception as e:
        print(f"❌ Error generating quote: {e}")
        raise HTTPException(status_code=500, detail=f"Quote generation failed: {str(e)}")

# -------------------------------------------------
# Endpoint: Generate Image (GET for cron jobs)
# -------------------------------------------------
@app.get("/generateimage", response_model=ImageResponse)
async def generate_image_endpoint(
    quote_file: str = "generated_quote.txt",
    template_path: str = "template.jpg",
    output_path: str = "image.jpg"
):
    """
    Creates a neon-style quote image from generated_quote.txt file.
    This is a GET endpoint for easy cron job triggering.
    Maximum wait time: 2 minutes.
    
    Query Parameters:
        quote_file: Path to quote file (default: generated_quote.txt)
        template_path: Path to template image (default: template.jpg)
        output_path: Path for output image (default: image.jpg)
        
    Returns:
        ImageResponse: Contains the output image path
    """
    try:
        # Read from file
        if not os.path.exists(quote_file):
            raise HTTPException(
                status_code=404,
                detail=f"Quote file not found: {quote_file}. Generate a quote first using /generatequote"
            )
        
        with open(quote_file, "r", encoding="utf-8") as f:
            quote_text = f.read().strip()
        
        if not quote_text:
            raise HTTPException(
                status_code=400,
                detail="Quote file is empty. Generate a quote first using /generatequote"
            )
        
        print(f"🎨 Creating neon image from file ({quote_file}): {quote_text[:50]}...")
        
        # Check if template exists
        if not os.path.exists(template_path):
            raise HTTPException(
                status_code=404,
                detail=f"Template file not found: {template_path}"
            )
        
        # Generate the image
        create_neon_quote_image(
            raw_text=quote_text,
            template_path=template_path,
            output_path=output_path
        )
        
        # Verify the output was created
        if not os.path.exists(output_path):
            raise HTTPException(
                status_code=500,
                detail="Image generation failed: output file not created"
            )
        
        print(f"✅ Image created: {output_path}")
        return ImageResponse(
            output_path=output_path,
            success=True,
            message=f"Image generated successfully using quote: {quote_text[:50]}..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

# -------------------------------------------------
# Endpoint: Upload to Facebook (GET for cron jobs)
# -------------------------------------------------
@app.get("/fbupload", response_model=FBUploadResponse)
async def fb_upload_endpoint(
    image_path: str = "image.jpg",
    caption: str = "",
    hours: int = 0,
    minutes: int = 0
):
    """
    Uploads an image to Facebook and returns the CDN URL.
    This is a GET endpoint for easy cron job triggering.
    Maximum wait time: 2 minutes.
    
    Query Parameters:
        image_path: Path to image file (default: image.jpg)
        caption: Photo caption (default: empty)
        hours: Schedule hours from now (default: 0 = immediate)
        minutes: Schedule minutes from now (default: 0 = immediate)
        
    Returns:
        FBUploadResponse: Contains the Facebook CDN URL
    """
    try:
        print(f"📤 Uploading to Facebook: {image_path}...")
        
        # Check if image exists
        if not os.path.exists(image_path):
            raise HTTPException(
                status_code=404,
                detail=f"Image file not found: {image_path}"
            )
        
        # Upload to Facebook
        fb_cdn_url = schedule_photo_after(
            image_path=image_path,
            caption=caption,
            hours=hours,
            minutes=minutes
        )
        
        if not fb_cdn_url:
            raise HTTPException(
                status_code=500,
                detail="Facebook upload failed: no CDN URL returned"
            )
        
        print(f"✅ Facebook upload successful: {fb_cdn_url}")
        return FBUploadResponse(
            fb_cdn_url=fb_cdn_url,
            success=True,
            message="Image uploaded to Facebook successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error uploading to Facebook: {e}")
        raise HTTPException(status_code=500, detail=f"Facebook upload failed: {str(e)}")

# -------------------------------------------------
# Endpoint: Upload to Instagram (Not a GET - requires FB URL)
# -------------------------------------------------
# Note: This endpoint remains POST as it requires a dynamic FB CDN URL
# Use /publish endpoint for cron jobs instead
@app.post("/igupload", response_model=IGUploadResponse)
async def ig_upload_endpoint(request: IGUploadRequest):
    """
    Posts an image to Instagram using a Facebook CDN URL.
    Maximum wait time: 2 minutes.
    
    Args:
        request: IGUploadRequest with fb_image_url and optional caption
        
    Returns:
        IGUploadResponse: Contains the Instagram post ID
    """
    try:
        print(f"📱 Publishing to Instagram from URL: {request.fb_image_url}...")
        
        # Post to Instagram
        ig_result = post_to_instagram_from_fb_url(
            fb_image_url=request.fb_image_url,
            caption=request.caption
        )
        
        ig_post_id = ig_result.get("id")
        if not ig_post_id:
            raise HTTPException(
                status_code=500,
                detail=f"Instagram publish failed: {ig_result}"
            )
        
        print(f"✅ Instagram post published: {ig_post_id}")
        return IGUploadResponse(
            post_id=ig_post_id,
            success=True,
            message="Image posted to Instagram successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error posting to Instagram: {e}")
        raise HTTPException(status_code=500, detail=f"Instagram upload failed: {str(e)}")

# -------------------------------------------------
# Background Task Function
# -------------------------------------------------
def execute_full_pipeline(caption: str, template_path: str, output_path: str):
    """
    Executes the full pipeline in the background.
    This runs asynchronously after the endpoint returns.
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
        # Step 1: Generate Quote
        logger.info("🚀 BACKGROUND TASK STARTED")
        logger.info("📝 Step 1/4: Generating AI quote...")
        
        quote_text = generate_quote()
        
        if not quote_text or not quote_text.strip():
            logger.error("❌ Quote generation failed")
            print(f"[{datetime.now()}] ❌ Quote generation failed", flush=True)
            return
        
        with open("generated_quote.txt", "w", encoding="utf-8") as f:
            f.write(quote_text)
        
        steps["quote_generated"] = True
        logger.info(f"✅ Quote generated: {quote_text[:50]}...")
        print(f"[{datetime.now()}] ✅ Quote generated: {quote_text[:50]}...", flush=True)
        
        # Step 2: Create Image
        logger.info("🎨 Step 2/4: Creating neon image...")
        print(f"[{datetime.now()}] 🎨 Step 2/4: Creating neon image...", flush=True)
        
        if not os.path.exists(template_path):
            logger.error(f"❌ Template not found: {template_path}")
            print(f"[{datetime.now()}] ❌ Template not found: {template_path}", flush=True)
            return
        
        create_neon_quote_image(
            raw_text=quote_text,
            template_path=template_path,
            output_path=output_path
        )
        
        if not os.path.exists(output_path):
            logger.error("❌ Image generation failed")
            print(f"[{datetime.now()}] ❌ Image generation failed", flush=True)
            return
        
        steps["image_created"] = True
        logger.info(f"✅ Image created: {output_path}")
        print(f"[{datetime.now()}] ✅ Image created: {output_path}", flush=True)
        
        # Step 3: Upload to Facebook
        logger.info("📤 Step 3/4: Uploading to Facebook...")
        print(f"[{datetime.now()}] 📤 Step 3/4: Uploading to Facebook...", flush=True)
        
        fb_cdn_url = schedule_photo_after(
            image_path=output_path,
            caption=caption,
            hours=0,
            minutes=0
        )
        
        if not fb_cdn_url:
            logger.error("❌ Facebook upload failed")
            print(f"[{datetime.now()}] ❌ Facebook upload failed", flush=True)
            return
        
        steps["facebook_uploaded"] = True
        logger.info(f"✅ Facebook upload successful: {fb_cdn_url}")
        print(f"[{datetime.now()}] ✅ Facebook upload successful: {fb_cdn_url}", flush=True)
        
        # Step 4: Publish to Instagram
        logger.info("📱 Step 4/4: Publishing to Instagram...")
        print(f"[{datetime.now()}] 📱 Step 4/4: Publishing to Instagram...", flush=True)
        
        ig_result = post_to_instagram_from_fb_url(
            fb_image_url=fb_cdn_url,
            caption=caption
        )
        
        ig_post_id = ig_result.get("id", "")
        
        if not ig_post_id:
            logger.warning("⚠️ Instagram publish failed (FB succeeded)")
            return
        
        steps["instagram_published"] = True
        logger.info(f"✅ Instagram post published: {ig_post_id}")
        logger.info("🎉 FULL PIPELINE COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        logger.error(f"Steps completed: {steps}")

# -------------------------------------------------
# Endpoint: Full Pipeline - ONE URL for Cron Jobs!
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
    logger.info("⚡ /autopilot endpoint called - adding background task")
    
    # Add the pipeline execution to background tasks
    background_tasks.add_task(
        execute_full_pipeline,
        caption=caption,
        template_path=template_path,
        output_path=output_path
    )
    
    logger.info("✅ Background task queued successfully")
    
    # Return immediately to prevent cron timeout
    return {
        "status": "accepted",
        "message": "Pipeline started in background. Check Render logs for progress.",
        "timestamp": datetime.now().isoformat(),
        "estimated_completion": "1-2 minutes",
        "log_instructions": "Go to Render Dashboard → Your Service → Logs tab to see real-time progress",
        "steps": [
            "1. Generate AI quote",
            "2. Create neon image",
            "3. Upload to Facebook",
            "4. Publish to Instagram"
        ]
    }

# -------------------------------------------------
# Endpoint: Upload to Both Facebook & Instagram (GET for cron jobs)
# -------------------------------------------------
@app.get("/publish", response_model=SocialMediaUploadResponse)
async def publish_to_social_media(
    image_path: str = "image.jpg",
    caption: str = "",
    hours: int = 0,
    minutes: int = 0
):
    """
    Uploads image to Facebook, gets CDN URL, then publishes to Instagram.
    This is a GET endpoint for easy cron job triggering.
    Perfect for automated posting workflows.
    Maximum wait time: 2 minutes.
    
    Query Parameters:
        image_path: Path to image file (default: image.jpg)
        caption: Photo caption for both platforms (default: empty)
        hours: Schedule hours from now (default: 0 = immediate)
        minutes: Schedule minutes from now (default: 0 = immediate)
        
    Returns:
        SocialMediaUploadResponse: Contains FB CDN URL, IG post ID, and status for both
    """
    fb_cdn_url = None
    ig_post_id = None
    
    try:
        # Step 1: Check if image exists
        if not os.path.exists(image_path):
            raise HTTPException(
                status_code=404,
                detail=f"Image file not found: {image_path}"
            )
        
        print(f"📤 Step 1/2: Uploading to Facebook: {image_path}...")
        
        # Step 2: Upload to Facebook
        fb_cdn_url = schedule_photo_after(
            image_path=image_path,
            caption=caption,
            hours=hours,
            minutes=minutes
        )
        
        if not fb_cdn_url:
            raise HTTPException(
                status_code=500,
                detail="Facebook upload failed: no CDN URL returned"
            )
        
        print(f"✅ Facebook upload successful: {fb_cdn_url}")
        
        # Step 3: Post to Instagram using FB CDN URL
        print(f"📱 Step 2/2: Publishing to Instagram from FB CDN URL...")
        
        ig_result = post_to_instagram_from_fb_url(
            fb_image_url=fb_cdn_url,
            caption=caption
        )
        
        ig_post_id = ig_result.get("id")
        if not ig_post_id:
            # Facebook succeeded but Instagram failed
            return SocialMediaUploadResponse(
                fb_cdn_url=fb_cdn_url,
                ig_post_id="",
                success=False,
                message="Facebook upload succeeded, but Instagram publish failed",
                fb_status="success",
                ig_status="failed"
            )
        
        print(f"✅ Instagram post published: {ig_post_id}")
        print("🎉 Successfully published to both Facebook and Instagram!")
        
        return SocialMediaUploadResponse(
            fb_cdn_url=fb_cdn_url,
            ig_post_id=ig_post_id,
            success=True,
            message="Image successfully published to both Facebook and Instagram",
            fb_status="success",
            ig_status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error during social media publish: {e}")
        
        # Return partial success if FB worked but IG failed
        if fb_cdn_url:
            return SocialMediaUploadResponse(
                fb_cdn_url=fb_cdn_url,
                ig_post_id="",
                success=False,
                message=f"Facebook upload succeeded, but Instagram failed: {str(e)}",
                fb_status="success",
                ig_status="failed"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Social media publish failed: {str(e)}"
            )

# -------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------
@app.get("/health")
async def health_check():
    """
    Simple health check endpoint to verify API is running.
    """
    return {
        "status": "healthy",
        "message": "Quote to Social Media API is running",
        "cron_endpoints": [
            "GET /autopilot - 🚀 FULL PIPELINE (quote → image → FB → IG)",
            "GET /generatequote - Generate AI quote only",
            "GET /generateimage - Create neon image only",
            "GET /publish - Upload to FB + IG only",
            "GET /fbupload - Upload to FB only"
        ],
        "api_endpoints": [
            "POST /igupload - Upload to IG (requires FB URL)"
        ]
    }

# -------------------------------------------------
# Root Endpoint
# -------------------------------------------------
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Quote to Social Media API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }

# -------------------------------------------------
# Run the API
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server...")
    print("📖 API Documentation available at: http://localhost:8000/docs")
    print("🔍 Health check available at: http://localhost:8000/health")
    # Use PORT from environment variable for Render compatibility
    port = int(os.environ.get("PORT", 8000))
    # Set timeout to 2 minutes (120 seconds) for all requests
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=120)

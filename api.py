from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
from QuoteGeneration import generate_quote
from ImageGeneration import create_neon_quote_image
from FBUpload import schedule_photo_after, post_to_instagram_from_fb_url

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
    quote_text: str
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

# -------------------------------------------------
# Endpoint: Generate Quote
# -------------------------------------------------
@app.get("/generatequote", response_model=QuoteResponse)
async def generate_quote_endpoint():
    """
    Generates a motivational quote using AI.
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
        
        print(f"✅ Quote generated: {quote_text[:50]}...")
        return QuoteResponse(
            quote=quote_text,
            success=True,
            message="Quote generated successfully"
        )
        
    except Exception as e:
        print(f"❌ Error generating quote: {e}")
        raise HTTPException(status_code=500, detail=f"Quote generation failed: {str(e)}")

# -------------------------------------------------
# Endpoint: Generate Image
# -------------------------------------------------
@app.post("/generateimage", response_model=ImageResponse)
async def generate_image_endpoint(request: ImageRequest):
    """
    Creates a neon-style quote image from text.
    Maximum wait time: 2 minutes.
    
    Args:
        request: ImageRequest with quote_text and optional paths
        
    Returns:
        ImageResponse: Contains the output image path
    """
    try:
        print(f"🎨 Creating neon image with quote: {request.quote_text[:50]}...")
        
        # Check if template exists
        if not os.path.exists(request.template_path):
            raise HTTPException(
                status_code=404,
                detail=f"Template file not found: {request.template_path}"
            )
        
        # Generate the image
        create_neon_quote_image(
            raw_text=request.quote_text,
            template_path=request.template_path,
            output_path=request.output_path
        )
        
        # Verify the output was created
        if not os.path.exists(request.output_path):
            raise HTTPException(
                status_code=500,
                detail="Image generation failed: output file not created"
            )
        
        print(f"✅ Image created: {request.output_path}")
        return ImageResponse(
            output_path=request.output_path,
            success=True,
            message="Image generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

# -------------------------------------------------
# Endpoint: Upload to Facebook
# -------------------------------------------------
@app.post("/fbupload", response_model=FBUploadResponse)
async def fb_upload_endpoint(request: FBUploadRequest):
    """
    Uploads an image to Facebook and returns the CDN URL.
    Maximum wait time: 2 minutes.
    
    Args:
        request: FBUploadRequest with image_path and optional scheduling
        
    Returns:
        FBUploadResponse: Contains the Facebook CDN URL
    """
    try:
        print(f"📤 Uploading to Facebook: {request.image_path}...")
        
        # Check if image exists
        if not os.path.exists(request.image_path):
            raise HTTPException(
                status_code=404,
                detail=f"Image file not found: {request.image_path}"
            )
        
        # Upload to Facebook
        fb_cdn_url = schedule_photo_after(
            image_path=request.image_path,
            caption=request.caption,
            hours=request.hours,
            minutes=request.minutes
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
# Endpoint: Upload to Instagram
# -------------------------------------------------
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
        "endpoints": [
            "/generatequote",
            "/generateimage",
            "/fbupload",
            "/igupload"
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
    # Set timeout to 2 minutes (120 seconds) for all requests
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=120)

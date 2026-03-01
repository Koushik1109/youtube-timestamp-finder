from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import google.generativeai as genai
import os
import time
import tempfile
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("✅ Gemini API configured successfully")
else:
    logger.warning("⚠️ GOOGLE_API_KEY not found - AI features will not work")


class SearchRequest(BaseModel):
    video_url: str
    topic: str


@app.post("/ask")
async def ask_fast(request: SearchRequest):
    """
    Find the timestamp when a topic is mentioned in a YouTube video.
    """
    temp_audio_path = None
    uploaded_file = None
    
    try:
        logger.info(f"📥 Received request:")
        logger.info(f"   Video: {request.video_url}")
        logger.info(f"   Topic: {request.topic}")
        
        # Check if API key is configured
        if not GOOGLE_API_KEY:
            raise HTTPException(
                status_code=500, 
                detail="GOOGLE_API_KEY environment variable not set"
            )
        
        # Step 1: Download audio from YouTube
        logger.info("⬇️ Step 1: Downloading audio from YouTube...")
        temp_audio_path = download_audio(request.video_url)
        logger.info(f"✅ Audio downloaded: {os.path.getsize(temp_audio_path)} bytes")
        
        # Step 2: Upload audio to Gemini Files API
        logger.info("📤 Step 2: Uploading audio to Gemini Files API...")
        uploaded_file = upload_to_gemini(temp_audio_path)
        logger.info(f"✅ File uploaded: {uploaded_file.name}")
        
        # Step 3: Wait for file to be processed
        logger.info("⏳ Step 3: Waiting for file to be processed...")
        wait_for_file_active(uploaded_file)
        logger.info("✅ File is ACTIVE and ready")
        
        # Step 4: Ask Gemini to find the timestamp
        logger.info("🤖 Step 4: Asking Gemini to find timestamp...")
        timestamp = find_timestamp_with_gemini(uploaded_file, request.topic)
        logger.info(f"✅ Found timestamp: {timestamp}")
        
        # Validate timestamp format
        if not validate_timestamp_format(timestamp):
            logger.warning(f"⚠️ Invalid timestamp format: {timestamp}, fixing...")
            timestamp = fix_timestamp_format(timestamp)
        
        return {
            "timestamp": timestamp,
            "video_url": request.video_url,
            "topic": request.topic
        }
        
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"❌ YouTube download error: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to download video: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temporary files
        cleanup(temp_audio_path, uploaded_file)


def download_audio(video_url: str) -> str:
    """
    Download audio from YouTube video using yt-dlp.
    Returns the path to the downloaded audio file.
    """
    # Create temporary file for audio
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    # Configure yt-dlp to download audio only
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'extract_audio': True,
    }
    
    # Download the audio
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    
    # yt-dlp may append .mp3 extension
    if not os.path.exists(temp_path) and os.path.exists(temp_path + '.mp3'):
        temp_path = temp_path + '.mp3'
    
    if not os.path.exists(temp_path):
        raise Exception("Failed to download audio file")
    
    return temp_path


def upload_to_gemini(audio_path: str):
    """
    Upload audio file to Gemini Files API.
    Returns the uploaded file object.
    """
    uploaded_file = genai.upload_file(
        path=audio_path,
        display_name="youtube_audio"
    )
    return uploaded_file


def wait_for_file_active(uploaded_file, max_wait: int = 120):
    """
    Wait for the uploaded file to be processed and become ACTIVE.
    """
    wait_time = 0
    while uploaded_file.state.name == "PROCESSING":
        if wait_time >= max_wait:
            raise Exception(f"File processing timeout after {max_wait} seconds")
        
        time.sleep(2)
        wait_time += 2
        uploaded_file = genai.get_file(uploaded_file.name)
        logger.info(f"   File state: {uploaded_file.state.name} (waited {wait_time}s)")
    
    if uploaded_file.state.name != "ACTIVE":
        raise Exception(f"File processing failed with state: {uploaded_file.state.name}")


def find_timestamp_with_gemini(uploaded_file, topic: str) -> str:
    """
    Use Gemini to analyze the audio and find when the topic is mentioned.
    Returns timestamp in HH:MM:SS format.
    """
    # Define structured output schema
    response_schema = {
        "type": "object",
        "properties": {
            "timestamp": {
                "type": "string",
                "description": "Timestamp in HH:MM:SS format (e.g., 00:05:47, 01:34:09)"
            }
        },
        "required": ["timestamp"]
    }
    
    # Create detailed prompt
    prompt = f"""You are analyzing an audio file from a YouTube video. Your task is to find the EXACT timestamp when a specific topic is first mentioned or discussed.

Topic to find: "{topic}"

INSTRUCTIONS:
1. Listen carefully to the entire audio
2. Identify when "{topic}" is first mentioned, discussed, or becomes the main subject
3. Return the timestamp in STRICT HH:MM:SS format with leading zeros

FORMAT REQUIREMENTS:
- MUST use HH:MM:SS format (hours:minutes:seconds)
- Include hours even if the video is less than 1 hour long
- Use leading zeros (e.g., 00:05:47, not 0:5:47)

EXAMPLES OF CORRECT FORMAT:
- 00:00:23 (23 seconds into the video)
- 00:05:47 (5 minutes and 47 seconds)
- 01:34:09 (1 hour, 34 minutes, and 9 seconds)
- 02:15:30 (2 hours, 15 minutes, and 30 seconds)

Find the FIRST meaningful occurrence of this topic in the audio."""

    # Use Gemini 2.0 Flash (recommended for audio)
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
    except:
        # Fallback to 1.5 Pro if 2.0 not available
        model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Generate response with structured output
    response = model.generate_content(
        [uploaded_file, prompt],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.1,  # Low temperature for consistent output
        )
    )
    
    # Parse JSON response
    result = json.loads(response.text)
    timestamp = result.get("timestamp", "00:00:00")
    
    return timestamp


def validate_timestamp_format(timestamp: str) -> bool:
    """
    Validate that timestamp is in correct HH:MM:SS format.
    """
    import re
    # Must match HH:MM:SS with exactly 2 digits for each part
    pattern = r'^\d{2}:\d{2}:\d{2}$'
    return bool(re.match(pattern, timestamp))


def fix_timestamp_format(timestamp: str) -> str:
    """
    Try to fix common timestamp format issues.
    """
    import re
    
    # Remove any extra whitespace
    timestamp = timestamp.strip()
    
    # If it's MM:SS, convert to HH:MM:SS
    if re.match(r'^\d{1,2}:\d{2}$', timestamp):
        parts = timestamp.split(':')
        return f"00:{parts[0].zfill(2)}:{parts[1]}"
    
    # If it's H:MM:SS or HH:M:SS or HH:MM:S, pad with zeros
    if re.match(r'^\d{1,2}:\d{1,2}:\d{1,2}$', timestamp):
        parts = timestamp.split(':')
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
    
    # If we can't fix it, return a default
    logger.warning(f"Could not fix timestamp format: {timestamp}")
    return "00:00:00"


def cleanup(temp_audio_path: str, uploaded_file):
    """
    Clean up temporary files and Gemini uploads.
    """
    # Delete local temporary file
    if temp_audio_path and os.path.exists(temp_audio_path):
        try:
            os.remove(temp_audio_path)
            logger.info(f"🗑️ Cleaned up temporary file: {temp_audio_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean up temp file: {e}")
    
    # Delete file from Gemini
    if uploaded_file:
        try:
            genai.delete_file(uploaded_file.name)
            logger.info(f"🗑️ Deleted file from Gemini: {uploaded_file.name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete Gemini file: {e}")


@app.get("/")
async def root():
    """Health check endpoint."""
    api_status = "✅ Configured" if GOOGLE_API_KEY else "❌ Not configured"
    return {
        "status": "ok",
        "message": "YouTube Timestamp Finder API",
        "endpoint": "POST /ask",
        "gemini_api": api_status
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "gemini_configured": bool(GOOGLE_API_KEY)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

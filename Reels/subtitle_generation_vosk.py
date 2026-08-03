"""
subtitle_generation_vosk.py

Generate subtitles using Vosk (Whisper-free alternative)

Vosk advantages:
- Free & offline
- Lightweight: ~50MB model
- Fast: Real-time capable
- Low memory: Perfect for Render free tier
- Word-level timestamps

pip install vosk
"""

import json
import wave
import os
import logging
import re
from pathlib import Path
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# Model cache directory
VOSK_MODEL_DIR = os.path.expanduser("~/.cache/vosk")
MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"

# Global model cache
_MODEL = None


def _ensure_model():
    """
    Download Vosk model if not cached.
    Uses small English model (40MB) for memory efficiency.
    """
    model_path = Path(VOSK_MODEL_DIR) / MODEL_NAME
    
    if model_path.exists():
        logger.info(f"✅ Using cached Vosk model: {MODEL_NAME}")
        return str(model_path)
    
    logger.info(f"📥 Downloading Vosk model: {MODEL_NAME} (~40MB)...")
    logger.info(f"This is a one-time download, model will be cached")
    
    # Create cache directory
    Path(VOSK_MODEL_DIR).mkdir(parents=True, exist_ok=True)
    
    # Download and extract
    import urllib.request
    import zipfile
    
    zip_path = Path(VOSK_MODEL_DIR) / f"{MODEL_NAME}.zip"
    
    try:
        urllib.request.urlretrieve(MODEL_URL, zip_path)
        logger.info(f"✅ Downloaded model")
        
        logger.info(f"📦 Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(VOSK_MODEL_DIR)
        
        # Clean up zip
        zip_path.unlink()
        
        logger.info(f"✅ Vosk model ready: {model_path}")
        return str(model_path)
        
    except Exception as e:
        logger.error(f"❌ Failed to download Vosk model: {e}")
        raise


def _get_model():
    """
    Lazy load Vosk model on first use.
    """
    global _MODEL
    
    if _MODEL is None:
        try:
            from vosk import Model
            model_path = _ensure_model()
            logger.info(f"🔊 Loading Vosk model...")
            _MODEL = Model(model_path)
            logger.info("✅ Vosk model loaded successfully")
        except ImportError:
            logger.error("❌ Vosk not installed. Run: pip install vosk")
            raise
    
    return _MODEL


def _convert_to_wav(audio_path):
    """
    Convert audio to WAV format required by Vosk.
    Returns path to temporary WAV file.
    """
    # Check if already WAV with correct format
    try:
        with wave.open(audio_path, 'rb') as wf:
            if (wf.getnchannels() == 1 and 
                wf.getsampwidth() == 2 and 
                wf.getframerate() == 16000):
                logger.info("✅ Audio already in correct format")
                return audio_path
    except:
        pass
    
    # Convert using ffmpeg
    logger.info("🔄 Converting audio to WAV (16kHz, mono)...")
    
    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_wav.close()
    
    try:
        subprocess.run([
            'ffmpeg',
            '-i', audio_path,
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',       # Mono
            '-y',             # Overwrite
            temp_wav.name
        ], check=True, capture_output=True)
        
        logger.info(f"✅ Converted to: {temp_wav.name}")
        return temp_wav.name
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FFmpeg conversion failed: {e}")
        raise


def _transcribe_with_vosk(wav_path):
    """
    Transcribe audio using Vosk and return word-level results.
    """
    from vosk import KaldiRecognizer
    
    model = _get_model()
    
    wf = wave.open(wav_path, "rb")
    
    # Create recognizer with word timestamps
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    
    results = []
    
    logger.info("🎤 Transcribing audio...")
    
    # Process audio in chunks
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if 'result' in result:
                results.extend(result['result'])
    
    # Get final result
    final_result = json.loads(rec.FinalResult())
    if 'result' in final_result:
        results.extend(final_result['result'])
    
    wf.close()
    
    logger.info(f"✅ Transcription complete: {len(results)} words")
    
    return results


def _build_natural_phrase_chunks(words):
    """
    Group words based on natural speech pauses.
    Similar logic to Whisper version.
    """
    if not words:
        return []
    
    chunks = []
    current_words = []
    current_start = None
    current_end = None
    
    for word_data in words:
        word = word_data.get('word', '').strip()
        start = word_data.get('start', 0)
        end = word_data.get('end', start)
        
        if not word:
            continue
        
        if current_start is None:
            current_start = start
        
        current_words.append(word)
        current_end = end
        
        # Create chunk at punctuation or after pause
        has_punctuation = any(p in word for p in ['.', '!', '?', ',', ';'])
        
        # Detect pause (gap > 0.5s)
        next_pause = False
        idx = words.index(word_data)
        if idx + 1 < len(words):
            next_start = words[idx + 1].get('start', end)
            next_pause = (next_start - end) > 0.5
        
        if has_punctuation or next_pause or len(current_words) >= 10:
            chunks.append({
                "start": current_start,
                "end": current_end,
                "text": " ".join(current_words)
            })
            current_words = []
            current_start = None
    
    # Add remaining words
    if current_words:
        chunks.append({
            "start": current_start,
            "end": current_end,
            "text": " ".join(current_words)
        })
    
    return chunks


def _split_long_chunks(chunks, max_words=8):
    """
    Split overly long chunks into smaller ones.
    """
    result = []
    
    for chunk in chunks:
        words = chunk["text"].split()
        
        if len(words) <= max_words:
            result.append(chunk)
            continue
        
        # Split long chunk
        start_time = chunk["start"]
        end_time = chunk["end"]
        total_duration = end_time - start_time
        time_per_word = total_duration / len(words) if words else 0
        
        for i in range(0, len(words), max_words):
            sub_words = words[i:i + max_words]
            sub_start = start_time + (i * time_per_word)
            sub_end = start_time + ((i + len(sub_words)) * time_per_word)
            
            result.append({
                "start": sub_start,
                "end": sub_end,
                "text": " ".join(sub_words)
            })
    
    return result


def generate_subtitles(audio_path):
    """
    Generate subtitles using Vosk (Whisper-free).
    
    Returns list of dicts with format:
    [
        {"start": 0.5, "end": 2.3, "text": "Hello world"},
        ...
    ]
    """
    logger.info(f"🎬 Generating subtitles with Vosk: {audio_path}")
    
    # Convert audio to correct format
    wav_path = _convert_to_wav(audio_path)
    temp_file = (wav_path != audio_path)
    
    try:
        # Transcribe with word timestamps
        words = _transcribe_with_vosk(wav_path)
        
        # Build natural chunks
        subtitles = _build_natural_phrase_chunks(words)
        
        # Split long chunks
        subtitles = _split_long_chunks(subtitles, max_words=8)
        
        logger.info(f"✅ Generated {len(subtitles)} subtitle segments")
        
        return subtitles
        
    finally:
        # Clean up temp WAV if created
        if temp_file:
            try:
                os.unlink(wav_path)
            except:
                pass


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python subtitle_generation_vosk.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    subs = generate_subtitles(audio_file)
    
    print(f"\nGenerated {len(subs)} subtitles:\n")
    for s in subs:
        print(f"[{s['start']:.2f} -> {s['end']:.2f}] {s['text']}")

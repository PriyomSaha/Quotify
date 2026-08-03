"""
subtitle_generation.py

Generate subtitles synced with narration pauses and natural speech flow.

pip install openai-whisper
ffmpeg required
"""

import whisper
import re


MODEL = whisper.load_model("base")


def _build_natural_phrase_chunks(segments):
    """
    Group words based on natural speech pauses and punctuation.
    Respects sentence boundaries, commas, and pauses in speech.
    """
    chunks = []
    
    for segment in segments:
        words = segment.get("words", [])
        text = segment.get("text", "").strip()
        
        if not words or not text:
            continue
        
        # Split by natural punctuation boundaries
        sentences = re.split(r'([.!?]\s+|,\s+|;\s+)', text)
        
        current_words = []
        current_start = None
        current_end = None
        word_index = 0
        
        for sentence_part in sentences:
            if not sentence_part.strip():
                continue
            
            # Count words in this sentence part
            part_words = sentence_part.strip().split()
            
            # Collect corresponding word timestamps
            for _ in range(len(part_words)):
                if word_index >= len(words):
                    break
                
                word = words[word_index]
                word_text = word.get("word", "").strip()
                
                if not word_text:
                    word_index += 1
                    continue
                
                if current_start is None:
                    current_start = word.get("start", 0)
                
                current_words.append(word_text)
                current_end = word.get("end", current_start)
                word_index += 1
            
            # Create chunk at sentence/punctuation boundary
            if current_words:
                chunks.append({
                    "start": current_start,
                    "end": current_end,
                    "text": " ".join(current_words)
                })
                current_words = []
                current_start = None
                current_end = None
        
        # Handle any remaining words in segment
        if current_words:
            chunks.append({
                "start": current_start,
                "end": current_end,
                "text": " ".join(current_words)
            })
    
    return chunks


def _split_long_chunks(chunks, max_words=8):
    """
    Split overly long chunks into smaller ones while respecting word boundaries.
    Ensures subtitles don't have too much text on screen.
    """
    result = []
    
    for chunk in chunks:
        words = chunk["text"].split()
        
        if len(words) <= max_words:
            result.append(chunk)
            continue
        
        # Split long chunk into smaller ones
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
    Generate subtitles that sync with natural speech flow.
    Respects pauses, punctuation, and sentence boundaries.
    """
    result = MODEL.transcribe(
        audio_path,
        word_timestamps=True
    )

    segments = result.get("segments", [])
    
    if not segments:
        return []
    
    # Build chunks based on natural speech pauses
    subtitles = _build_natural_phrase_chunks(segments)
    
    # Split any overly long chunks (max 8 words)
    subtitles = _split_long_chunks(subtitles, max_words=8)
    
    return subtitles


if __name__ == "__main__":

    subs = generate_subtitles("voice.mp3")

    for s in subs:
        print(s)
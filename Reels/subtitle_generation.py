"""
subtitle_generation.py

Generate short, punchy subtitles using Whisper.

pip install openai-whisper
ffmpeg required
"""

import whisper


MODEL = whisper.load_model("base")


def _build_short_phrase_chunks(words, max_words=4):
    """
    Group words into short phrases of 3-4 words for better Reel captions.
    """

    chunks = []
    current = []
    chunk_start = None
    chunk_end = None

    for word in words:
        text = word.get("word", "").strip()
        if not text:
            continue

        if chunk_start is None:
            chunk_start = word.get("start", 0)

        current.append(text)
        chunk_end = word.get("end", chunk_start)

        if len(current) >= max_words:
            chunks.append({
                "start": chunk_start,
                "end": chunk_end,
                "text": " ".join(current)
            })
            current = []
            chunk_start = None
            chunk_end = None

    if current:
        chunks.append({
            "start": chunk_start if chunk_start is not None else 0,
            "end": chunk_end if chunk_end is not None else 0,
            "text": " ".join(current)
        })

    return chunks


def generate_subtitles(audio_path):

    result = MODEL.transcribe(
        audio_path,
        word_timestamps=True
    )

    subtitles = []
    all_words = []

    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            all_words.append(word)

    if not all_words:
        return subtitles

    subtitles = _build_short_phrase_chunks(all_words, max_words=4)

    return subtitles


if __name__ == "__main__":

    subs = generate_subtitles("voice.mp3")

    for s in subs:
        print(s)
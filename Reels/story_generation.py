"""
story_generation.py

Generates short-form viral narration content for Instagram Reels.

Output:
- Story / Poem / Observation
- Structured JSON
- 6 visual scenes
- Character definition
- Visual style definition

Requires:
pip install google-genai
"""

from typing import Dict, Any
from google import genai
from .config import GEMINI_API_KEY, GEMINI_MODEL
from .PromptSelector import get_prompt_for_current_time , BASE_INSTRUCTION
from .gender_tracker import get_next_gender, get_gender_instruction
import json

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL = GEMINI_MODEL

def build_generation_prompt() -> str:

    # Get the complete prompt (returns a string, not a dict)
    final_prompt = get_prompt_for_current_time()
    
    # Pick a random visual mode
    visual_mode = get_next_gender()
    visual_instruction = get_gender_instruction(visual_mode)

    print(f"\n🎭 Visual mode for this reel: {visual_mode.upper()}")
    
    # Note: content info is already printed in PromptSelector.get_prompt_for_current_time()
    # No need to import or call get_content_type_for_time again

    # Add JSON output format requirements to the prompt
    return f"""
        {final_prompt}

        ==================================================
        OUTPUT FORMAT

        Return ONLY valid JSON.

        {{
            "content_type": "",
            "title": "",
            "narration": "",
            "visual_style": {{
                "art_style": "cinematic painterly editorial illustration",
                "palette": "",
                "lighting": "",
                "camera": "",
                "aspect_ratio": "9:16"
            }},
            "visual_mode": "{visual_mode}",
            "character": {{
                "gender": "",
                "age": "",
                "hair": "",
                "clothes": ""
            }},
            "scenes": [
                "",
                "",
                "",
                "",
                "",
                ""
            ]
        }}

        ==================================================
        JSON RULES

        - narration must contain 80-110 words
        - narration must strictly follow the selected content category
        - exactly 6 visual scenes
        - each scene must represent one clear visual moment
        - every scene must directly match the narration
        - follow the selected visual mode exactly: {visual_mode}
        - male and female should be treated equally; do not prefer either gender
        - use the same main character throughout all scenes only when the visual mode uses a character
        - if no character is needed, keep the emotional world consistent through place, color, weather, objects, or nature
        - scenes must be illustration-friendly and visually varied
        - avoid repeating the same location unless intentional
        - avoid sunset as the default; use varied natural aesthetics like rain, morning mist, moonlight, cloudy afternoon, warm indoor lamps, forest shade, blue hour, monsoon reflections, snow, or soft dawn
        - avoid making every scene a lonely man looking at sunset

        ==================================================
        CHARACTER RULES

        {visual_instruction}

        General rules:
        - Ordinary people only if the selected visual mode needs people
        - No celebrities, no fantasy characters, no glamour portraits, no selfies
        - Use realistic, simple, relatable clothes when humans appear
        - Prefer medium/wide cinematic shots over close-up faces
        - Include natural or meaningful elements: plants, rain, birds, fields, rivers, windows, books, cups, letters, lamps, roads, balconies, buses, libraries, train stations
        - Avoid stereotypes and clichés

        ==================================================
        VISUAL STYLE

        Keep the illustration style consistent for all scenes.

        Art Style:
        cinematic painterly editorial illustration with soft natural textures.
        Ghibli-style can be used when it fits the reel, but keep it randomized and not mandatory every time.

        Aspect Ratio:
        9:16

        ==================================================
        IMPORTANT

        Return ONLY valid JSON.

        Do NOT wrap the JSON inside markdown.

        Do NOT explain anything.

        Do NOT add extra text before or after the JSON.
        """


def generate_story_json():
    """
    Generate story JSON from Gemini, or use a local fallback if credentials are missing.
    """

    print("Generating story...")

    # if client is None or not GEMINI_API_KEY:
    #     print("GEMINI_API_KEY missing. Using demo story fallback.")
    #     return get_demo_story_json()

    try:
        prompt = build_generation_prompt()

        interaction = client.interactions.create(
            model=MODEL,
            input=prompt
        )

        if interaction.output_text is None:
            raise ValueError("Gemini returned empty response.")

        return parse_story_json(interaction.output_text)

    except Exception as exc:
        print(f"Gemini call failed: {exc}")
        print("Using demo story fallback.")
        return get_demo_story_json()


def get_demo_story_json():
    """
    Fallback demo story when Gemini API fails.
    """
    return {
        "content_type": "QUIET_MEMORY",
        "title": "The Things That Stay",
        "narration": "Some memories do not need people inside them to feel alive. A cup left near the window. Rain touching the balcony plants. An old book opening by itself in the fan's wind. We think love disappears when life changes, but sometimes it only changes shape. It becomes the light on the floor, the song from another room, the empty chair we still do not move. The heart remembers quietly, even when the world keeps walking.",
        "visual_style": {
            "art_style": "cinematic painterly editorial illustration",
            "palette": "soft earthy greens, warm lamp light, muted rain blues",
            "lighting": "rainy window light and warm indoor glow",
            "camera": "medium-wide poetic still frames",
            "aspect_ratio": "9:16"
        },
        "visual_mode": "object",
        "character": {
            "gender": "none",
            "age": "N/A",
            "hair": "N/A",
            "clothes": "N/A"
        },
        "scenes": [
            "A half-full tea cup beside a rainy apartment window, balcony plants blurred outside",
            "An old book open on a wooden table while curtain shadows move across the pages",
            "A small lamp glowing beside a photo frame turned slightly away",
            "Rain drops sliding down glass with city lights reflected softly in the background",
            "An empty chair near a quiet window with fallen leaves on the floor",
            "Morning light entering the same room, touching the tea cup and open book"
        ]
    }


import json


def parse_story_json(raw_text: str) -> Dict[str, Any]:
    """
    Parse Gemini JSON response.
    """

    text = raw_text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1)

    if text.startswith("```"):
        text = text.replace("```", "", 1)

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse Gemini JSON.\n\n{text}"
        ) from e

    validate_story_json(data)

    return data


def validate_story_json(data: Dict[str, Any]) -> None:
    """
    Validate generated JSON.
    """

    required = [
        "content_type",
        "title",
        "narration",
        "visual_style",
        "character",
        "scenes"
    ]

    for field in required:
        if field not in data:
            raise ValueError(
                f"Missing field: {field}"
            )

    narration = data["narration"].strip()

    words = len(narration.split())

    if words < 80 or words > 120:
        raise ValueError(
            f"Narration must be between 80-120 words. Current: {words}"
        )

    scenes = data["scenes"]

    if not isinstance(scenes, list):
        raise ValueError("Scenes must be a list.")

    if len(scenes) != 6:
        raise ValueError(
            f"Exactly 6 scenes required. Got {len(scenes)}"
        )

    style = data["visual_style"]

    style_required = [
        "art_style",
        "palette",
        "lighting",
        "camera",
        "aspect_ratio"
    ]

    for field in style_required:
        if field not in style:
            raise ValueError(
                f"visual_style missing '{field}'"
            )

    character = data["character"]

    character_required = [
        "gender",
        "age",
        "hair",
        "clothes"
    ]

    for field in character_required:
        if field not in character:
            raise ValueError(
                f"character missing '{field}'"
            )


def generate_story() -> Dict[str, Any]:
    """
    Public function used by the pipeline.
    """

    story = generate_story_json()

    print("Story generated successfully.")

    print(f"Type      : {story['content_type']}")
    print(f"Title     : {story['title']}")
    print(f"Scenes    : {len(story['scenes'])}")
    print(
        f"Words     : {len(story['narration'].split())}"
    )

    return story

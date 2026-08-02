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
from config import GEMINI_API_KEY, GEMINI_MODEL
from PromptSelector import get_prompt_for_current_time , BASE_INSTRUCTION
import json

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL = GEMINI_MODEL

def build_generation_prompt() -> str:

    # Get the complete prompt (returns a string, not a dict)
    final_prompt = get_prompt_for_current_time()
    
    # Get content info for display
    from PromptSelector import get_content_type_for_time
    content_info = get_content_type_for_time()

    print(f"\n📝 Generating : {content_info['category']}")
    print(f"💡 {content_info['mood']}")

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
                "art_style": "minimal flat editorial illustration",
                "palette": "",
                "lighting": "",
                "camera": "",
                "aspect_ratio": "9:16"
            }},
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
        - use the same main character throughout all scenes
        - if no character is needed, keep the environment consistent
        - scenes must be illustration-friendly
        - avoid repeating the same location unless intentional

        ==================================================
        CHARACTER RULES

        - maximum two characters
        - ordinary people only
        - realistic appearance
        - consistent clothing
        - consistent hairstyle
        - consistent age
        - consistent gender

        ==================================================
        VISUAL STYLE

        Keep the illustration style consistent for all scenes.

        Art Style:
        minimal flat editorial illustration

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
        "content_type": "QUIET_LOVE",
        "title": "Two Cups of Tea",
        "narration": "Nobody noticed the old man at the tea stall. Every evening he ordered two cups. One for himself. One for someone who never came. The shop owner finally asked why. The old man smiled. My wife passed away five years ago. But memories don't check calendars. Some habits become another way of saying I still love you.",
        "visual_style": {
            "art_style": "minimal flat editorial illustration",
            "palette": "warm sepia tones with soft orange sunset glow",
            "lighting": "golden hour, soft shadows",
            "camera": "medium shots, intimate framing",
            "aspect_ratio": "9:16"
        },
        "character": {
            "gender": "male",
            "age": "70s",
            "hair": "grey, neatly combed",
            "clothes": "simple kurta, worn sweater"
        },
        "scenes": [
            "Old man sitting alone at a small tea stall, evening light",
            "Two steaming cups of tea on a wooden table",
            "Shop owner looking at the old man with curiosity",
            "Old man's gentle smile, holding one cup",
            "Empty chair beside him with tea cup",
            "Old man walking away slowly, sunset in background"
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

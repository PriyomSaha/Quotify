import base64
import io
import json
import os
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from dotenv import load_dotenv

from event_detector import build_event_image_instruction
from .config import OUTPUT_DIR

load_dotenv()

# ============================================================
# CLOUDFLARE CONFIG
# ============================================================

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID_1")
CF_TOKEN = os.getenv("CF_TOKEN_1")

CF_ACCOUNT_ID_2 = os.getenv("CF_ACCOUNT_ID_2")
CF_TOKEN_2 = os.getenv("CF_TOKEN_2")

CF_MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"

CLOUDFLARE_URL_TEMPLATE = (
    "https://api.cloudflare.com/client/v4/accounts/"
    "{account_id}/ai/run/"
    f"{CF_MODEL}"
)

QUOTA_STATUS_CODE = 429

CLOUDFLARE_ACCOUNTS = [
    {
        "name": "Primary",
        "account_id": CF_ACCOUNT_ID,
        "api_token": CF_TOKEN,
    },
    {
        "name": "Secondary",
        "account_id": CF_ACCOUNT_ID_2,
        "api_token": CF_TOKEN_2,
    },
]

CLOUDFLARE_ACCOUNTS = [
    account
    for account in CLOUDFLARE_ACCOUNTS
    if account["account_id"] and account["api_token"]
]

if not CLOUDFLARE_ACCOUNTS:
    raise RuntimeError("No Cloudflare accounts configured.")

# ============================================================
# REEL SETTINGS
# ============================================================

REEL_WIDTH = 1080
REEL_HEIGHT = 1920

# ============================================================
# IMAGE STYLE
# ============================================================

BASE_STYLE_PROMPT = """
Create a beautiful cinematic digital painting.

Clean, culturally specific, and symbol-driven visual storytelling.

Painterly brush strokes.

Soft natural textures.

Natural atmospheric lighting that matches the scene.

Rich but realistic colors.

Emotional storytelling through iconic symbols, places, atmosphere, and meaningful national or cultural context.

Premium cinematic composition.

Highly detailed environment.

Natural perspective.

Award-winning illustration.

Movie still.

Professional composition.

Vertical 9:16.

No text.
"""

STYLE_VARIATIONS = [
    "Japanese slice-of-life anime film look, hand-painted background art, peaceful everyday emotion.",
    "Cinematic painterly editorial illustration, natural textures, grounded emotional realism.",
    "Dreamy animated movie background style, lush plants, soft clouds, warm nostalgic color palette.",
    "Watercolor-like painterly illustration, quiet poetic atmosphere, delicate light and shadow.",
    "Soft Ghibli-style animated film mood, hand-painted backgrounds, whimsical nature, gentle character design.",
    "Hand-painted 2D illustration, soft watercolor and gouache textures, delicate linework, cinematic composition, warm nostalgic mood, expressive painted backgrounds, rich natural colors, non-photorealistic."
]

NEGATIVE_PROMPT = """
text,
letters,
caption,
logo,
watermark,
signature,
frame,
border,
low quality,
blurry,
pixelated,
cropped,
duplicate people,
multiple heads,
extra arms,
extra legs,
extra fingers,
bad anatomy,
deformed,
distorted,
mutated,
3d,
cgi,
render,
photograph,
photorealistic,
generic cozy home interior,
cozy family room,
small wooden cabin,
house exterior,
bungalow,
balcony scene,
window-view apartment,
tea stall,
coffee shop,
old city lane,
random rainy street,
generic apartment balcony for no reason
"""

# ============================================================
# ENVIRONMENT POOL
# ============================================================

ENVIRONMENTS = [
    "misty pine forest",
    "peaceful mountain overlook",
    "empty countryside road after rain",
    "rainy city street with soft reflections",
    "cozy coffee shop window",
    "small wooden cabin surrounded by trees",
    "old train station in quiet morning light",
    "forest trail with wet leaves",
    "ocean shore under cloudy sky",
    "wildflower field with soft wind",
    "wooden dock beside a still lake",
    "old bridge over a narrow river",
    "snow covered path through trees",
    "library corner with window light",
    "empty park bench under trees",
    "cliff overlooking the sea",
    "river bank with smooth stones",
    "lighthouse during blue hour",
    "village street after monsoon rain",
    "balcony with plants and curtain shadows",
    "rooftop garden in soft dawn light",
    "quiet bus stop after rainfall",
    "tea stall beside a wet road",
    "moonlit lake with gentle ripples",
    "empty classroom with afternoon light",
    "narrow old city lane with plants",
]

LIGHTING = [
    "soft dawn light",
    "warm morning light",
    "cloudy afternoon light",
    "blue hour",
    "gentle rain light",
    "after rainfall glow",
    "moonlight",
    "warm indoor lamp light",
    "monsoon window light",
    "forest shade with light beams",
    "winter morning haze",
    "muted overcast daylight",
]

MOODS = [
    "peaceful",
    "nostalgic",
    "quiet",
    "melancholic",
    "hopeful",
    "reflective",
    "comforting",
    "dreamlike",
]

FOREGROUND_DETAILS = [
    "wildflowers",
    "fallen leaves",
    "wooden fence",
    "rain puddles",
    "grass",
    "tea cup",
    "open book",
    "lantern",
    "old bicycle",
    "window",
    "birds",
    "balcony plants",
    "paper letter",
    "old diary",
    "umbrella",
    "bus ticket",
    "photo frame",
    "curtain shadows",
    "fireflies",
    "butterflies",
    "smooth river stones",
]

# ============================================================
# PROMPT HELPERS
# ============================================================

MAX_PROMPT_LENGTH = 1800


def normalize_prompt_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact_prompt(text: str) -> str:
    text = normalize_prompt_text(text)
    if len(text) > MAX_PROMPT_LENGTH:
        text = text[:MAX_PROMPT_LENGTH].rstrip()
    return text

# ============================================================
# PROMPT BUILDER
# ============================================================

def build_style_prompt(event_mode: bool = False) -> str:
    """Return the base style, with event mode avoiding cozy generic default imagery."""
    if event_mode:
        return (
            f"{BASE_STYLE_PROMPT}\n\n"
            "Event-first artistic direction:\n"
            "Use iconic occasion symbols and clear visual identity. "
            "Do not default to cozy home interiors, balcony scenes, cabin settings, or generic rainy-city imagery unless the occasion itself requires them. "
            "The image must clearly communicate what the event is famous for. "
            "Ghibli-style elements are integrated throughout—hand-painted backgrounds, whimsical nature, and gentle character design."
        )

    return f"{BASE_STYLE_PROMPT}\n\nStyle variation:\n{STYLE_VARIATIONS[0]}"


def build_prompt_for_normal_day(
    scene_type: str,
    scene_description: str,
) -> str:
    """Build prompt for normal days with random environment, lighting, mood, and foreground variations."""
    scene_type = (scene_type or "environment").lower().strip()
    scene_description = (scene_description or "").strip()

    if scene_type == "couple":
        subject = (
            "Two people naturally interacting. "
            "Walking together, sitting quietly, holding hands, sharing an umbrella, "
            "or enjoying a peaceful moment. "
            "No close-up faces. Natural body language."
        )

    elif scene_type == "person":
        subject = (
            "One person naturally inside the environment. "
            "Walking, reading, drinking coffee, sitting by a window, "
            "watching the rain, standing on a bridge, looking at the sky, "
            "or enjoying nature. "
            "Not a portrait. Never a selfie."
        )

    elif scene_type == "object":
        subject = (
            "An everyday object tells the story. "
            "Books, tea, coffee, bicycle, lantern, flowers, window, "
            "umbrella, camera, diary, wooden chair, phone, bus ticket, keys, shoes, lamp, photo frame or similar. "
            "No human characters."
        )

    elif scene_type == "architecture":
        subject = (
            "Beautiful architecture or interior space. "
            "Coffee shop, library, train station, bridge, tea stall, classroom, bus stop, quiet street or other public place. "
            "The place itself carries the emotion."
        )

    elif scene_type == "animal_life":
        subject = (
            "Gentle natural life is the main subject. "
            "Birds, stray cat, sleeping dog, butterflies, fireflies, deer, fish ripples, or cows on a quiet road. "
            "Peaceful, realistic, symbolic. No fantasy animals."
        )

    elif scene_type == "rainy_city":
        subject = (
            "Rainy city atmosphere is the main subject. "
            "Wet roads, umbrellas, bus windows, balcony plants, tea stalls, apartment windows, neon reflections, and puddles. "
            "People may be tiny and distant only."
        )

    elif scene_type == "nostalgic_room":
        subject = (
            "A nostalgic room or memory-filled interior tells the story. "
            "Old desk, curtains, warm lamp, photo frame, empty chair, open notebook, window light, plants, childhood objects. "
            "No human characters."
        )

    elif scene_type == "abstract_emotion":
        subject = (
            "Emotion is shown through concrete environments, light, shadow, weather, doors, windows, roads, water, seasons, and empty spaces. "
            "No human characters. Keep it poetic but clear."
        )

    else:
        subject = (
            "Environment is the main subject. "
            "Nature tells the story through forests, rivers, fields, sky, rain, wind, flowers, stones, clouds, moonlight, and soft natural movement. "
            "No human characters unless explicitly required by the scene."
        )

    # For normal days: use random variations
    environment = random.choice(ENVIRONMENTS)
    lighting = random.choice(LIGHTING)
    mood = random.choice(MOODS)
    foreground = random.choice(FOREGROUND_DETAILS)

    variation = cinematic_variation()

    prompt = f"""
        {build_style_prompt(event_mode=False)}

        Scene:
        {scene_description}

        Subject:
        {subject}

        Environment:
        {environment}

        Lighting:
        {lighting}

        Mood:
        {mood}

        Foreground:
        {foreground}

        Composition:
        Vertical 9:16.
        {variation["camera"]}.
        {variation["lens"]}.
        Professional cinematic framing.
        Layered foreground, middle ground and background.
        Natural depth.
        Balanced composition.
        Leave clean negative space for subtitles.

        Quality:
        Highly detailed.
        Painterly illustration.
        Soft brush strokes.
        Rich textures.
        Natural colors.
        Sharp focus.
        Beautiful lighting appropriate to the scene, not always sunset.
        Clean edges.
        Emotional storytelling.
        Movie still.
        Award-winning artwork.

        Avoid:
        No text.
        No logo.
        No watermark.
        No blurry image.
        No low quality.
        No cropped subject.
        No duplicate people.
        No deformed anatomy.
        No extra fingers.
        No extra limbs.
        No CGI.
        No 3D render.
        No photorealistic photo.
        """

    return compact_prompt(prompt)


def build_prompt_for_event(
    scene_type: str,
    scene_description: str,
    event_instruction: str,
    event_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Build prompt for event days with event-specific visual cues from calendar data."""
    scene_type = (scene_type or "environment").lower().strip()
    scene_description = (scene_description or "").strip()
    event_instruction = (event_instruction or "").strip()

    # Sanitize scene description for events: remove generic/conflicting elements
    scene_description_clean = scene_description
    
    # Remove generic keywords that contradict event focus
    generic_keywords_to_remove = {
        "dog", "cat", "animal", "quiet", "resting", "sleeping",
        "coffee shop", "tea stall", "library", "classroom", "bus stop",
        "balcony", "cabin", "home", "house", "cozy", "interior",
        "rainy", "monsoon", "puddle", "umbrella", "car", "lady", "woman",
        "man", "person", "people",
    }
    
    words = scene_description_clean.lower().split()
    filtered_words = [
        word for word in words 
        if not any(generic in word.lower() for generic in generic_keywords_to_remove)
    ]
    
    if filtered_words:
        scene_description_clean = " ".join(filtered_words).strip()
    
    # If cleaning removed too much, use event instruction as base
    if not scene_description_clean or len(scene_description_clean) < 15:
        scene_description_clean = event_instruction

    # Extract styling from event calendar data
    camera_angle = "wide establishing shot"
    lens_style = "35mm film lens"
    weather_style = "golden light"
    color_grade = "vibrant natural colors"
    style_variation = "Bold cinematic visual storytelling with cultural pride and national symbolism."
    
    if event_data:
        camera_angle = event_data.get("camera_angle", camera_angle)
        lens_style = event_data.get("lens_style", lens_style)
        weather_style = event_data.get("weather", weather_style)
        color_grade = event_data.get("color_grade", color_grade)
        style_variation = event_data.get("style_variation", style_variation)

    # Build ASSERTIVE event prompt with MANDATORY event focus
    prompt = f"""
CRITICAL: This image MUST represent {event_instruction}
DO NOT generate random, generic, or unrelated content.
Every element must serve the event narrative.

{build_style_prompt(event_mode=True)}

MANDATORY EVENT FOCUS:
{event_instruction}

This is the primary visual identity. Prioritize event-specific symbols, landmarks, colors, and cultural elements above all else.

Scene Context:
{scene_description_clean}

Style Direction:
{style_variation}

Composition:
Vertical 9:16 reel format.
{camera_angle}.
{lens_style}.
Professional cinematic framing with clear visual hierarchy.
Bold, memorable imagery that immediately communicates the event.

Lighting & Atmosphere:
{weather_style}
Natural, warm, celebratory mood matching the occasion.

Color Palette:
{color_grade}
Use culturally significant colors prominently.

Quality Standards:
Highly detailed, award-winning illustration.
Soft painterly style with rich textures.
Sharp focus. Movie-quality composition.
Emotional depth matching the event significance.

CRITICAL NEGATIVES - DO NOT GENERATE:
- Random cars, vehicles, or transportation
- Random people (men, women, children) unrelated to event
- Generic coffee shops, homes, offices
- Rainy or mundane weather unless event-specific
- Abstract vague imagery
- Anything that doesn't directly support the event narrative
- Low quality, blurry, or poorly rendered content
- Text, logos, watermarks, or signatures
        """

    return compact_prompt(prompt)


def build_prompt(
    scene_type: Optional[str] = None,
    scene_description: Optional[str] = None,
    event_instruction: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Backward compatibility wrapper.
    Routes to build_prompt_for_event() if event_instruction is provided,
    otherwise to build_prompt_for_normal_day().
    """
    # Normalize optional parameters to strings
    scene_type_str = (scene_type or "environment").lower().strip()
    scene_description_str = (scene_description or "").strip()
    event_instruction_str = (event_instruction or "").strip()
    
    if event_instruction_str:
        return build_prompt_for_event(
            scene_type=scene_type_str,
            scene_description=scene_description_str,
            event_instruction=event_instruction_str,
            event_data=event_data,
        )
    else:
        return build_prompt_for_normal_day(
            scene_type=scene_type_str,
            scene_description=scene_description_str,
        )


# ============================================================
# CLOUDFLARE IMAGE GENERATION
# ============================================================

def generate_image_with_cloudflare(
    prompt: str,
    event_mode: bool = False,
) -> Optional[Image.Image]:
    prompt = compact_prompt(prompt)
    negative_prompt = compact_prompt(NEGATIVE_PROMPT)

    if event_mode:
        steps = 8
        guidance = 12.0
        negative_prompt = compact_prompt(
            NEGATIVE_PROMPT
            + ", random people, random cars, random vehicles, random objects, random animals, "
            + "generic home scene, balcony with plants, cabin, bungalow, cozy room, rainy city street, "
            + "tea stall, coffee shop, apartment interior, abstract vague imagery, unclear composition, "
            + "unrelated subject matter, off-topic content, random lady, random man, random woman, "
            + "random child, random stranger, random face, random portrait, low resolution, poorly rendered"
        )
    else:
        steps = random.choice([5, 6, 7])
        guidance = random.choice([3.5, 4.0, 4.5, 5.0])

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "guidance": guidance,
    }

    print(f"\nCloudflare prompt (event_mode={event_mode}):\n{prompt[:1200]}\n")

    for account in CLOUDFLARE_ACCOUNTS:
        print(f"\nUsing Cloudflare Account: {account['name']}")

        try:
            response = requests.post(
                CLOUDFLARE_URL_TEMPLATE.format(
                    account_id=account["account_id"]
                ),
                headers={
                    "Authorization": f"Bearer {account['api_token']}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=180,
            )

        except requests.RequestException as exc:
            print(f"Network Error: {exc}")
            continue

        if response.status_code == QUOTA_STATUS_CODE:
            print("Quota exceeded. Trying next account...")
            continue

        # if response.status_code != 200:
        #     print(f"HTTP {response.status_code}")
        #     try:
        #         print(response.json())
        #     except Exception:
        #         print(response.text)
        # try:
        #     result = response.json()

        #     if not result.get("success", True):
        #         print(result)
        #         continue

        #     image_b64 = (
        #         result
        #         .get("result", {})
        #         .get("image")
        #     )

        #     if not image_b64:
        #         print("No image returned.")
        #         continue

        #     image = Image.open(
        #         io.BytesIO(
        #             base64.b64decode(image_b64)
        #         )
        #     ).convert("RGB")

        #     print("✓ Image generated successfully")

        #     return image
        # except Exception as exc:
        #     print(f"Image Decode Error: {exc}")
        #     continue

        if response.status_code != 200:
            print(f"HTTP {response.status_code}")

            try:
                print(response.json())
            except Exception:
                print(response.text)

            continue

        try:
            # New Cloudflare model returns the actual PNG binary,
            # not JSON containing a Base64 image.
            image = Image.open(
                io.BytesIO(response.content)
            ).convert("RGB")

            print("✓ Image generated successfully")

            return image

        except Exception as exc:
            print(f"Image Decode Error: {exc}")
            continue
    print("\nAll Cloudflare accounts failed.")

    return None

# ============================================================
# IMAGE PROCESSING
# ============================================================

def enhance_natural_clarity(
    image: Image.Image,
) -> Image.Image:
    image = image.convert("RGB")

    image = ImageEnhance.Contrast(image).enhance(1.12)
    image = ImageEnhance.Color(image).enhance(1.08)
    image = ImageEnhance.Sharpness(image).enhance(1.18)

    image = image.filter(
        ImageFilter.UnsharpMask(
            radius=1.3,
            percent=110,
            threshold=3,
        )
    )

    return image


def apply_cinematic_grade(
    image: Image.Image,
) -> Image.Image:
    image = image.convert("RGB")

    image = ImageEnhance.Color(image).enhance(1.10)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Brightness(image).enhance(1.02)

    return image


def resize_for_reel(
    image: Image.Image,
) -> Image.Image:
    image = image.convert("RGB")

    width, height = image.size

    target_ratio = REEL_WIDTH / REEL_HEIGHT
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        image = image.crop(
            (
                left,
                0,
                left + new_width,
                height,
            )
        )

    elif current_ratio < target_ratio:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        image = image.crop(
            (
                0,
                top,
                width,
                top + new_height,
            )
        )

    image = image.resize(
        (
            REEL_WIDTH,
            REEL_HEIGHT,
        ),
        Image.Resampling.LANCZOS,
    )

    return image


def finalize_image(
    image: Image.Image,
) -> Image.Image:
    image = resize_for_reel(image)
    image = apply_cinematic_grade(image)
    image = enhance_natural_clarity(image)
    return image


# ============================================================
# SAVE IMAGE
# ============================================================

def save_image(
    image: Image.Image,
    output_path: str,
) -> str:
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image.save(
        output,
        format="PNG",
        optimize=True,
    )

    print(f"✓ Saved: {output}")

    return str(output)

# ============================================================
# SCENE DETECTION
# ============================================================

RELATIONSHIP_KEYWORDS = {
    "love",
    "lover",
    "couple",
    "relationship",
    "holding hands",
    "boy",
    "girl",
    "husband",
    "wife",
    "partner",
    "together",
    "two people",
    "friends",
}

PERSON_KEYWORDS = {
    "person",
    "man",
    "woman",
    "child",
    "friend",
    "traveler",
    "student",
    "father",
    "mother",
    "someone",
}

OBJECT_KEYWORDS = {
    "book",
    "tea",
    "coffee",
    "cup",
    "phone",
    "letter",
    "bicycle",
    "umbrella",
    "lantern",
    "flower",
    "camera",
    "chair",
    "window",
    "diary",
    "ticket",
    "keys",
    "shoes",
    "lamp",
    "photo frame",
    "notebook",
}

ARCHITECTURE_KEYWORDS = {
    "library",
    "cafe",
    "coffee shop",
    "station",
    "bridge",
    "room",
    "street",
    "classroom",
    "bus stop",
    "tea stall",
    "rooftop",
}

ANIMAL_KEYWORDS = {
    "bird",
    "birds",
    "cat",
    "dog",
    "butterfly",
    "butterflies",
    "fireflies",
    "deer",
    "fish",
    "cow",
    "cows",
    "animal",
}

RAINY_CITY_KEYWORDS = {
    "rainy city",
    "monsoon",
    "wet street",
    "puddle",
    "bus window",
    "umbrella",
    "neon reflection",
}

NOSTALGIC_ROOM_KEYWORDS = {
    "old room",
    "bedroom",
    "study desk",
    "curtain",
    "empty chair",
    "family photo",
    "warm lamp",
}

ENVIRONMENT_VARIATIONS = [
    "misty mountain lake at dawn",
    "peaceful ocean shore with gentle waves under cloudy sky",
    "forest trail after light rain",
    "green field beneath dramatic clouds",
    "snow covered mountain path",
    "river flowing through smooth rocks",
    "flower meadow in soft morning light",
    "empty countryside road after rainfall",
    "pine forest with low mist",
    "cliff overlooking the sea during blue hour",
    "moonlit lake with soft ripples",
    "rain drops on green leaves",
]

PERSON_VARIATIONS = [
    "walking quietly along a forest path",
    "reading a book beside a rainy window",
    "standing on a train platform in morning haze",
    "drinking coffee inside a cozy cafe",
    "standing on a bridge during blue hour",
    "looking across a peaceful lake under cloudy sky",
    "walking beneath autumn trees",
    "sitting on a quiet bus near a rain-streaked window",
    "watering balcony plants in soft morning light",
]

COUPLE_VARIATIONS = [
    "walking hand in hand along the beach",
    "sharing an umbrella during gentle rain",
    "sitting together on a wooden dock",
    "watching stars from a grassy hill",
    "walking through a flower field",
    "drinking coffee together near a large window",
]

OBJECT_VARIATIONS = [
    "old bicycle near wildflowers",
    "warm tea beside a rainy window",
    "open book on a wooden table",
    "camera resting on a backpack",
    "lantern glowing beside a cabin window",
    "umbrella beside a quiet wet street",
    "paper letter under warm lamp light",
    "bus ticket on an empty seat",
    "old diary with dried flowers",
    "photo frame beside balcony plants",
]

ARCHITECTURE_VARIATIONS = [
    "warm coffee shop interior",
    "peaceful old library",
    "wooden cabin surrounded by trees",
    "empty train station",
    "old lighthouse beside the sea",
    "quiet old city lane with plants",
    "small tea stall after rain",
    "empty classroom with afternoon light",
    "rooftop garden in soft dawn light",
]

ANIMAL_VARIATIONS = [
    "birds sitting on electric wires after rain",
    "stray cat sleeping near a tea stall",
    "dog resting outside a small shop",
    "butterflies moving through wildflowers",
    "fireflies glowing above wet grass",
    "deer standing near the edge of a forest",
    "fish ripples spreading across a quiet pond",
]

RAINY_CITY_VARIATIONS = [
    "rainy street with umbrella reflections",
    "bus window covered with raindrops",
    "tea stall glowing beside a wet road",
    "apartment balcony plants during monsoon rain",
    "empty bus stop after rainfall",
    "neon reflections in quiet puddles",
]

NOSTALGIC_ROOM_VARIATIONS = [
    "old study desk with warm lamp light",
    "curtains moving beside an open window",
    "empty chair near a family photo frame",
    "open notebook on a quiet bedroom floor",
    "plant shadows on a sunlit wall",
    "childhood books stacked near a window",
]

ABSTRACT_EMOTION_VARIATIONS = [
    "open door with soft light spilling into a dark room",
    "long empty road disappearing into morning mist",
    "window shadow moving slowly across the floor",
    "two seasons meeting through fallen leaves and new flowers",
    "ripples spreading across still water",
    "staircase lit by a single warm window",
]


def contains_keyword(
    text: str,
    keywords: set[str],
) -> bool:
    text = text.lower()
    return any(keyword in text for keyword in keywords)


def detect_scene_type(
    description: str,
    default: str = "environment",
) -> str:
    allowed_defaults = {
        "environment",
        "person",
        "couple",
        "object",
        "architecture",
        "animal_life",
        "rainy_city",
        "nostalgic_room",
        "abstract_emotion",
        "nature",
        "female",
        "male",
        "friends_or_couple",
    }
    if default not in allowed_defaults:
        default = "environment"

    if default == "female" or default == "male":
        default = "person"
    elif default == "friends_or_couple":
        default = "couple"
    elif default == "nature":
        default = "environment"

    if default in {"animal_life", "rainy_city", "nostalgic_room", "abstract_emotion"}:
        return default

    if contains_keyword(description, ANIMAL_KEYWORDS):
        return "animal_life"

    if contains_keyword(description, RAINY_CITY_KEYWORDS):
        return "rainy_city"

    if contains_keyword(description, NOSTALGIC_ROOM_KEYWORDS):
        return "nostalgic_room"

    if contains_keyword(description, RELATIONSHIP_KEYWORDS):
        return "couple"

    if contains_keyword(description, PERSON_KEYWORDS):
        return "person"

    if contains_keyword(description, OBJECT_KEYWORDS):
        return "object"

    if contains_keyword(description, ARCHITECTURE_KEYWORDS):
        return "architecture"

    return default


def random_scene_description(
    scene_type: str,
) -> str:
    if scene_type == "couple":
        return random.choice(COUPLE_VARIATIONS)

    if scene_type == "person":
        return random.choice(PERSON_VARIATIONS)

    if scene_type == "object":
        return random.choice(OBJECT_VARIATIONS)

    if scene_type == "architecture":
        return random.choice(ARCHITECTURE_VARIATIONS)

    if scene_type == "animal_life":
        return random.choice(ANIMAL_VARIATIONS)

    if scene_type == "rainy_city":
        return random.choice(RAINY_CITY_VARIATIONS)

    if scene_type == "nostalgic_room":
        return random.choice(NOSTALGIC_ROOM_VARIATIONS)

    if scene_type == "abstract_emotion":
        return random.choice(ABSTRACT_EMOTION_VARIATIONS)

    return random.choice(ENVIRONMENT_VARIATIONS)


GENERIC_EVENT_KW = {
    "house",
    "cabin",
    "balcony",
    "cozy",
    "home",
    "tea stall",
    "coffee shop",
    "rainy city",
    "wet street",
    "bus stop",
    "room",
    "classroom",
    "library",
    "bridge",
    "street",
    "forest trail",
    "quiet road",
    "old city lane",
}


def sanitize_event_scene_description(
    description: str,
    event_name: str,
) -> str:
    cleaned = str(description or "").strip()
    if not cleaned:
        return f"{event_name} celebration scene with iconic visual symbolism and strong cultural identity."

    lowered = cleaned.lower()
    if any(keyword in lowered for keyword in GENERIC_EVENT_KW):
        cleaned = ""

    if not cleaned:
        return f"{event_name} celebration scene using iconic festival visuals, national symbolism, and emotionally rich storytelling."

    return cleaned


def enhance_scene_for_variety(
    scene: Dict[str, Any],
    index: int,
    visual_mode: str = "environment",
    event: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    scene_type = str(
        scene.get("type") or visual_mode or "environment"
    ).lower()

    description = str(
        scene.get("description", "")
    ).strip()

    scene_type = detect_scene_type(
        description,
        scene_type,
    )

    if not description:
        description = random_scene_description(
            scene_type
        )

    if event:
        event_name = str(event.get("name", "special occasion")).strip() or "special occasion"
        event_instruction = build_event_image_instruction(event)
        description = sanitize_event_scene_description(description, event_name)
        description = (
            f"{event_instruction} "
            f"{description}. "
            "Cinematic composition. Painterly illustration. Highly detailed. Beautiful natural colors. Emotional storytelling. No text."
        )
        return {
            "type": "event",
            "description": description,
        }

    lighting = random.choice(LIGHTING)
    mood = random.choice(MOODS)
    foreground = random.choice(FOREGROUND_DETAILS)

    description += (
        f". Lighting: {lighting}."
        f" Mood: {mood}."
        f" Foreground: {foreground}."
        " Cinematic composition."
        " Painterly illustration."
        " Highly detailed."
        " Beautiful natural colors."
        " Emotional storytelling."
        " No text."
        " Do not default to sunset unless the scene explicitly needs it."
    )

    return {
        "type": scene_type,
        "description": description,
    }


# ============================================================
# PLACEHOLDER IMAGE
# ============================================================

def create_placeholder_image(
    output_path: str,
    scene: str,
) -> str:
    output = Path(output_path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image = Image.new(
        "RGB",
        (REEL_WIDTH, REEL_HEIGHT),
        (35, 35, 40),
    )

    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (
            60,
            60,
            REEL_WIDTH - 60,
            REEL_HEIGHT - 60,
        ),
        outline=(120, 120, 120),
        width=4,
    )

    draw.text(
        (90, 120),
        "IMAGE GENERATION FAILED",
        fill=(255, 255, 255),
    )

    draw.text(
        (90, 200),
        scene[:250],
        fill=(190, 190, 190),
    )

    image.save(output, optimize=True)

    return str(output)

# ============================================================
# SINGLE IMAGE GENERATION
# ============================================================

def generate_single_image(
    scene: Dict[str, Any],
    output_path: str,
    event_instruction: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
) -> str:
    scene_type = scene.get("type", "environment")
    scene_description = scene.get("description", "").strip()

    print("\n" + "=" * 60)
    print("GENERATING IMAGE")
    print("=" * 60)
    print(f"Type : {scene_type}")
    print(f"Scene: {scene_description}")

    prompt = build_prompt(
        scene_type=scene_type,
        scene_description=scene_description,
        event_instruction=event_instruction,
        event_data=event_data,
    )

    image = generate_image_with_cloudflare(
        prompt,
        event_mode=bool(event_instruction),
    )

    if image is None:
        print("Image generation failed. Using placeholder.")
        return create_placeholder_image(
            output_path,
            scene_description,
        )

    image = finalize_image(image)

    return save_image(
        image,
        output_path,
    )


# ============================================================
# GENERATE ALL IMAGES
# ============================================================

def generate_images_for_reel(
    reel_json: Dict[str, Any],
    output_dir: str | Path | None = None,
    prefix: str = "scene",
) -> List[str]:
    from event_detector import CONTENT_REEL, get_today_event

    event = get_today_event(content_type=CONTENT_REEL)
    event_instruction = build_event_image_instruction(event) if event else None

    if output_dir is None:
        output_dir = OUTPUT_DIR / "images"

    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    visual_mode = str(reel_json.get("visual_mode", "environment")).lower()
    character = reel_json.get("character", {}) or {}
    character_gender = str(character.get("gender", "")).lower()

    if not visual_mode or visual_mode == "environment":
        if character_gender in {"male", "female"}:
            visual_mode = character_gender
        elif character_gender == "none":
            visual_mode = "environment"

    scenes = reel_json.get("visual_scenes")

    if not scenes:
        scenes = reel_json.get("scenes", [])

        scenes = [
            {
                "type": visual_mode,
                "description": scene,
            }
            for scene in scenes
        ]

    if not scenes:
        raise ValueError("No scenes found.")

    print("\n" + "=" * 70)
    print("AESTHETIC VIBES IMAGE GENERATION")
    print("=" * 70)
    print(f"Scenes : {len(scenes)}")
    print(f"Output : {output_dir}")

    generated_images = []

    for index, scene in enumerate(
        scenes,
        start=1,
    ):
        scene = enhance_scene_for_variety(
            scene,
            index,
            visual_mode,
            event=event,
        )

        output_path = (
            output_dir /
            f"{prefix}_{index:02d}.png"
        )

        print("\n" + "-" * 70)
        print(f"Scene {index}/{len(scenes)}")
        print("-" * 70)

        image_path = generate_single_image(
            scene=scene,
            output_path=str(output_path),
            event_instruction=event_instruction,
            event_data=event,
        )

        generated_images.append(image_path)

    print("\n" + "=" * 70)
    print("IMAGE GENERATION COMPLETE")
    print("=" * 70)

    return generated_images

# ============================================================
# CINEMATIC VARIATIONS
# ============================================================

CAMERA_ANGLES = [
    "eye-level shot",
    "low-angle shot",
    "high-angle shot",
    "wide establishing shot",
    "over-the-shoulder composition",
    "side profile composition",
    "three-quarter composition",
    "distant cinematic view",
]

LENS_STYLES = [
    "24mm cinematic lens",
    "35mm film lens",
    "50mm natural perspective",
    "wide landscape lens",
]

WEATHER_STYLES = [
    "clear sky",
    "soft rain",
    "after rainfall",
    "blue hour",
    "early morning",
    "autumn afternoon",
    "winter morning",
    "monsoon clouds",
    "soft mist",
    "moonlit night",
    "cloudy afternoon",
]

COLOR_GRADES = [
    "soft pastel",
    "muted earthy colors",
    "cool blue evening",
    "warm indoor amber",
    "fresh rainy greens",
    "misty blue grey",
    "soft dawn peach",
    "natural film colors",
]

def cinematic_variation() -> Dict[str, str]:
    return {
        "camera": random.choice(CAMERA_ANGLES),
        "lens": random.choice(LENS_STYLES),
        "weather": random.choice(WEATHER_STYLES),
        "grade": random.choice(COLOR_GRADES),
    }
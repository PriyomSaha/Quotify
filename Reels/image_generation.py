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

from .config import OUTPUT_DIR

load_dotenv()

# ============================================================
# CLOUDFLARE CONFIG
# ============================================================

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID_1")
CF_TOKEN = os.getenv("CF_TOKEN_1")

CF_ACCOUNT_ID_2 = os.getenv("CF_ACCOUNT_ID_2")
CF_TOKEN_2 = os.getenv("CF_TOKEN_2")

CF_MODEL = "@cf/black-forest-labs/flux-1-schnell"

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

Japanese slice-of-life inspired illustration with South Asian everyday warmth.

Painterly brush strokes.

Soft natural textures.

Natural atmospheric lighting that matches the scene.

Rich but realistic colors.

Emotional storytelling through nature, objects, places, weather, and ordinary people.

Peaceful aesthetic atmosphere.

Highly detailed environment.

Natural perspective.

Award-winning illustration.

Movie still.

Professional composition.

Vertical 9:16.

No text.
"""

STYLE_VARIATIONS = [
    "Soft Ghibli-style animated film mood, hand-painted backgrounds, whimsical nature, gentle character design.",
    "Japanese slice-of-life anime film look, hand-painted background art, peaceful everyday emotion.",
    "Cinematic painterly editorial illustration, natural textures, grounded emotional realism.",
    "Dreamy animated movie background style, lush plants, soft clouds, warm nostalgic color palette.",
    "Watercolor-like painterly illustration, quiet poetic atmosphere, delicate light and shadow.",
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
photorealistic
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

def build_style_prompt() -> str:
    """Return the base style plus one random aesthetic variation."""
    return f"{BASE_STYLE_PROMPT}\n\nStyle variation:\n{random.choice(STYLE_VARIATIONS)}"


def build_prompt(
    scene_type: str,
    scene_description: str,
) -> str:
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
            "Coffee shop, library, train station, old cabin, balcony, "
            "wooden house, bridge, lighthouse, tea stall, classroom, bus stop or quiet street. "
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

    environment = random.choice(ENVIRONMENTS)
    lighting = random.choice(LIGHTING)
    mood = random.choice(MOODS)
    foreground = random.choice(FOREGROUND_DETAILS)
    variation = cinematic_variation()

    prompt = f"""
        {build_style_prompt()}

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

# ============================================================
# CLOUDFLARE IMAGE GENERATION
# ============================================================

def generate_image_with_cloudflare(
    prompt: str,
) -> Optional[Image.Image]:
    prompt = compact_prompt(prompt)
    negative_prompt = compact_prompt(NEGATIVE_PROMPT)

    steps = random.choice([5, 6, 7])
    guidance = random.choice([3.5,4.0, 4.5, 5.0])

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "guidance": guidance,
    }

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

        if response.status_code != 200:
            print(f"HTTP {response.status_code}")
            try:
                print(response.json())
            except Exception:
                print(response.text)
            continue

        try:
            result = response.json()

            if not result.get("success", True):
                print(result)
                continue

            image_b64 = (
                result
                .get("result", {})
                .get("image")
            )

            if not image_b64:
                print("No image returned.")
                continue

            image = Image.open(
                io.BytesIO(
                    base64.b64decode(image_b64)
                )
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
    "house",
    "home",
    "room",
    "balcony",
    "street",
    "cabin",
    "lighthouse",
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


def enhance_scene_for_variety(
    scene: Dict[str, Any],
    index: int,
    visual_mode: str = "environment",
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
    )

    image = generate_image_with_cloudflare(prompt)

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
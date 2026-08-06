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

STYLE_PROMPT = """
Create a beautiful cinematic digital painting.

Japanese slice-of-life inspired illustration.

Painterly brush strokes.

Soft natural textures.

Warm golden hour lighting.

Beautiful volumetric sunlight.

Natural shadows.

Rich but realistic colors.

Orange and teal cinematic grading.

Emotional storytelling.

Peaceful atmosphere.

Highly detailed environment.

Beautiful sky.

Soft clouds.

Natural perspective.

Award-winning illustration.

Movie still.

Professional composition.

Vertical 9:16.

No text.
"""

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
    "quiet lakeside at sunset",
    "peaceful mountain overlook",
    "empty countryside road",
    "rainy city street",
    "cozy coffee shop window",
    "small wooden cabin",
    "old train station",
    "forest trail",
    "ocean shore",
    "flower field",
    "wooden dock",
    "old bridge",
    "snow covered path",
    "library corner",
    "park bench",
    "cliff overlooking the sea",
    "river bank",
    "lighthouse",
    "village street",
    "balcony during sunset",
]

LIGHTING = [
    "golden hour",
    "soft sunset",
    "blue hour",
    "warm morning light",
    "gentle rain",
    "after rainfall",
    "moonlight",
    "cloudy afternoon",
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
            "umbrella, camera, diary, wooden chair or similar."
        )

    elif scene_type == "architecture":
        subject = (
            "Beautiful architecture or interior space. "
            "Coffee shop, library, train station, old cabin, balcony, "
            "wooden house, bridge, lighthouse or quiet street."
        )

    else:
        subject = (
            "Environment is the main subject. "
            "Nature tells the story."
        )

    environment = random.choice(ENVIRONMENTS)
    lighting = random.choice(LIGHTING)
    mood = random.choice(MOODS)
    foreground = random.choice(FOREGROUND_DETAILS)
    variation = cinematic_variation()

    prompt = f"""
        {STYLE_PROMPT}

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
        Beautiful lighting.
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
}

ENVIRONMENT_VARIATIONS = [
    "quiet mountain lake during sunset",
    "peaceful ocean shore with gentle waves",
    "forest trail after light rain",
    "golden wheat field beneath dramatic clouds",
    "snow covered mountain path",
    "river flowing through rocks",
    "flower meadow in warm evening light",
    "empty countryside road",
    "mist-free pine forest",
    "cliff overlooking the sea",
]

PERSON_VARIATIONS = [
    "walking quietly along a forest path",
    "reading a book beside a rainy window",
    "watching the sunset from a wooden dock",
    "drinking coffee inside a cozy cafe",
    "standing on a bridge during blue hour",
    "looking across a peaceful lake",
    "walking beneath autumn trees",
    "sitting on a lonely park bench",
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
    "lantern glowing during sunset",
    "umbrella beside a quiet street",
]

ARCHITECTURE_VARIATIONS = [
    "warm coffee shop interior",
    "peaceful old library",
    "wooden cabin surrounded by trees",
    "empty train station",
    "old lighthouse beside the sea",
    "traditional Japanese street",
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

    return random.choice(ENVIRONMENT_VARIATIONS)


def enhance_scene_for_variety(
    scene: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:
    scene_type = str(
        scene.get("type", "environment")
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

    scenes = reel_json.get("visual_scenes")

    if not scenes:
        scenes = reel_json.get("scenes", [])

        scenes = [
            {
                "type": "environment",
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
    "golden sunset",
    "blue hour",
    "early morning",
    "autumn afternoon",
    "winter morning",
]

COLOR_GRADES = [
    "warm orange and teal",
    "golden cinematic",
    "soft pastel",
    "muted earthy colors",
    "warm sunset colors",
    "cool blue evening",
]

def cinematic_variation() -> Dict[str, str]:
    return {
        "camera": random.choice(CAMERA_ANGLES),
        "lens": random.choice(LENS_STYLES),
        "weather": random.choice(WEATHER_STYLES),
        "grade": random.choice(COLOR_GRADES),
    }
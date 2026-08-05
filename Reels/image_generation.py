"""
image_generation.py

Aesthetic Vibes Image Generator

Creates cinematic hand-drawn editorial illustrations
for short wisdom reels.

Visual Identity

✓ Environment-first composition
✓ Tiny human silhouette
✓ Natural clear color palette
✓ Hand-drawn editorial artwork
✓ Large negative space for subtitles
✓ 1080x1920 Reel Ready
"""

import base64
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import random
import re

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
    "@cf/black-forest-labs/flux-1-schnell"
)

QUOTA_STATUS_CODE = 429

CLOUDFLARE_ACCOUNTS = [
    {
        "name": "Primary",
        "account_id": CF_ACCOUNT_ID,
        "api_token": CF_TOKEN,
    },
    {
        "name": "2nd Account",
        "account_id": CF_ACCOUNT_ID_2,
        "api_token": CF_TOKEN_2,
    }
]

if not CLOUDFLARE_ACCOUNTS:
    raise RuntimeError("No Cloudflare accounts configured.")

# ============================================================
# REEL SETTINGS
# ============================================================

REEL_WIDTH = 1080
REEL_HEIGHT = 1920

# ============================================================
# AESTHETIC VIBES VISUAL STYLE
# ============================================================

AESTHETIC_STYLE = """

Create a premium hand-drawn editorial illustration.

Traditional illustration.

Graphite pencil sketch.

Fine ink line art.

Controlled transparent watercolor shading with clear edges.

Subtle textured paper.

Natural brush strokes.

Visible handmade imperfections.

Elegant book illustration.

NOT cartoon.

NOT anime.

NOT comic.

NOT Pixar.

NOT Disney.

NOT vector art.

NOT 3D.

NOT photorealistic.

"""

# ============================================================
# CHANNEL ATMOSPHERE
# ============================================================

ATMOSPHERE = """

The image should feel calm.

Peaceful.

Quiet.

Thoughtful.

Emotionally mature.

Reflective.

Lonely without feeling depressing.

Warm but melancholic.

Minimal.

Timeless.

Everything feels slow.

Nothing dramatic.

Nothing exciting.

The viewer should pause and think.

"""

# ============================================================
# COLOR PALETTE
# ============================================================

COLOR_PALETTE = """

Natural earthy colors.

Clear sky blue.

Forest green.

Warm sunlight amber.

Soft sunset orange.

Dusty brown.

Natural stone grey.

Muted cream highlights.

Balanced saturation.

Clean cinematic color grading.

Golden hour.

Late sunset.

Soft moonlight.

Clear morning light.

Deep natural shadows.

No hazy grey overlay.

No foggy or misty wash.

"""

# ============================================================
# COMPOSITION
# ============================================================

COMPOSITION = """

The environment is the main subject.

Landscape occupies around 90% of the image.

The human occupies less than 10%.

Use an extreme wide cinematic shot.

Establishing shot.

Large negative space.

Large empty sky.

Large empty foreground.

Rule of thirds.

Professional movie composition.

Leave plenty of empty space for subtitles.

The scenery should tell the story.

"""

# ============================================================
# HUMAN
# ============================================================

HUMAN_STYLE = """

If a person appears:

Show only one person.

The person is tiny.

The person is a distant silhouette.

Never close to the camera.

Never portrait composition.

Never selfie.

Never looking at the viewer.

Show from behind or side.

Anonymous.

The person should simply exist inside the environment.

"""

# ============================================================
# ENVIRONMENTS
# ============================================================

ENVIRONMENTS = """

Choose environments naturally.

Quiet beach.

Ocean shoreline.

Lake.

River bank.

Mountain overlook.

Forest trail.

Clear quiet country road.

Country road.

Empty bridge.

Old wooden dock.

Rainy street.

Park bench.

Field during sunset.

Snow path.

Old library.

Wooden cabin.

Window during rain.

Coffee shop window.

Cliff.

Lighthouse.

Train station.

Night sky.

Stars.

Moon.

Clouds.

Tall grass.

Wild flowers.

Old trees.

Empty road.

"""

# ============================================================
# ENVIRONMENT DETAILS
# ============================================================

DETAILS = """

Use meaningful environmental details.

Birds flying.

Moonlight.

Stars.

Cloud movement.

Rain.

Clear air.

Wind.

Ocean waves.

Reflection on water.

Leaves.

Street lamps.

Telephone wires.

Boats.

Flowers.

Mountains.

Fireflies.

Distant lights.

Soft shadows.

"""

# ============================================================
# NEGATIVE PROMPT
# ============================================================

NEGATIVE_PROMPT = """

portrait

close-up

selfie

headshot

large face

person filling frame

multiple people

crowd

fashion photography

studio lighting

looking at camera

cartoon

anime

comic

pixar

disney

cgi

3d render

photorealistic

oversaturated colors

bright colorful scene

busy composition

repeated scene

duplicate composition

same background

overlapping subjects

cluttered foreground

action pose

dramatic pose

weapon

violence

text

letters

logo

watermark

caption

speech bubble

typography

blur

blurry

haze

hazy

fog

foggy

mist

misty

smoky atmosphere

washed out colors

muddy colors

grey veil

low contrast

out of focus

low quality

distorted hands

extra fingers

bad anatomy

duplicate face

"""

# ============================================================
# BRAND COLOR MODE - Toggle this to switch styles
# ============================================================
# Set to True for brand colors (pink/purple theme)
# Set to False for natural colors (current style)
USE_BRAND_COLORS = False  # ← Change this to False to revert

# ============================================================
# PROMPT BUILDER
# ============================================================

def build_prompt(
    scene_type: str,
    scene_description: str,
) -> str:
    """
    Build varied aesthetic image prompts.

    The goal is not to force the same "person facing back" frame every time.
    Most scenes should be nature/object/environment driven, with occasional
    human or couple scenes only when the story calls for it.
    """
    normalized_type = scene_type.lower().strip()

    if normalized_type == "couple":
        subject_instruction = """
Subject: two small human figures only if natural to the scene, for example a boy and girl holding hands, sitting apart on a bench, walking beside a lake, sharing an umbrella, or standing quietly near a sunset road.
Keep them tasteful and cinematic, not romantic-photo-shoot style.
No close-up faces. No selfie. No fashion pose. Show natural body language, hands, distance, warmth, and environment.
"""
    elif normalized_type == "person":
        subject_instruction = """
Subject: at most one small human figure, integrated naturally into the environment.
Avoid repeating the same back-facing silhouette. Vary the pose: side profile, sitting near a window, walking under trees, reading on a bench, holding flowers, looking down at water, tying shoelaces, holding an umbrella, or standing in soft side light.
Face can be simple/abstract, but not a close-up portrait.
"""
    elif normalized_type == "object":
        subject_instruction = """
Subject: a meaningful everyday object as the emotional focus, with nature around it.
Examples: two cups of tea, a blank open sketchbook with no visible writing, plain sealed envelopes with no text, a bicycle near flowers, shoes beside water, a lantern, a phone on a table with blank screen, a window with rain, a small boat, dried flowers.
No people unless absolutely necessary.
"""
    elif normalized_type == "architecture":
        subject_instruction = """
Subject: a quiet place or structure as the focus.
Examples: old library corner, rainy cafe window, empty train station, wooden cabin, bridge, lighthouse, balcony, narrow street, warm house window.
No people unless tiny and secondary.
"""
    else:
        subject_instruction = """
Subject: pure aesthetic nature/environment scene.
No human subject by default. Focus on landscape, sky, water, trees, flowers, road, clouds, moonlight, sunlight, reflections, and atmosphere.
"""

    if USE_BRAND_COLORS:
        color_instruction = """Natural cinematic colors with very subtle Aesthetic Vibes accents: muted pink highlights (#FF2075), deep burgundy shadows (#610B2D), natural sky blue, forest green, warm cream light. Keep it natural, clear, not neon, not oversaturated, not hazy."""
    else:
        color_instruction = """Natural cinematic colors: clear sky blue, forest green, warm sunlight amber, dusty brown, natural stone grey, soft cream, pale sky blue, gentle sunset orange. Balanced natural color grading, clean contrast, clear air, not blurred, not hazy, not foggy, not misty, not over-saturated."""

    return f"""
Premium hand-drawn editorial illustration for an emotional Instagram Reel.

Scene idea: {scene_description}

{subject_instruction}

Visual style:
- hand-drawn sketch illustration
- fine ink linework
- soft watercolor texture without haze
- subtle paper grain
- natural brush strokes
- clean readable shapes
- clear visible edges
- crisp details, not blurry, not foggy, not misty
- elegant book-cover / magazine editorial feeling

Composition:
- vertical 9:16 cinematic frame
- strong nature-first composition
- large negative space for subtitles
- rule of thirds
- layered depth with foreground, midground, background
- unique setting, angle, foreground detail, and subject placement for every scene
- avoid repetitive centered person from behind
- no overlapping main subjects; keep objects and people cleanly separated and readable
- make every scene feel visually different from the previous one

Atmosphere:
Calm, peaceful, reflective, warm, melancholic, emotionally mature, poetic but simple. The air should feel clear and crisp, never hazy, foggy, smoky, or washed out.

Natural elements:
Trees, wildflowers, quiet roads, lakes, rivers, ocean shore, gentle rain, moon, clean clouds, birds, window light, warm lamps, clear reflections, grass, mountains, old wood, blank paper, tea, books with no readable text.

Color direction:
{color_instruction}

Strict quality rules:
No text, no letters, no logo, no watermark, no speech bubble, no caption inside image.
No blurry image. No haze. No fog. No mist. No smoky atmosphere. No washed-out colors. No muddy grey overlay. No repeated background. No duplicate composition. No overlapping subjects. No cluttered foreground. No low quality. No distorted hands. No extra fingers. No duplicate faces.
Not cartoon, not anime, not 3D, not photorealistic, not stock photo.
"""

# ============================================================
# CLOUDFLARE IMAGE GENERATION
# ============================================================

def generate_image_with_cloudflare(
    prompt: str,
) -> Optional[Image.Image]:

    payload = {

        "prompt": prompt,

        "negative_prompt": NEGATIVE_PROMPT,

        "steps": 4,

        "guidance": 3.5,

    }

    for account in CLOUDFLARE_ACCOUNTS:

        try:

            print(f"\nUsing Cloudflare account: {account['name']}")

            url = CLOUDFLARE_URL_TEMPLATE.format(
                account_id=account["account_id"]
            )

            headers = {
                "Authorization": f"Bearer {account['api_token']}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=180,
            )

            if response.status_code == 200:

                result = response.json()

                if (
                    "result" in result
                    and "image" in result["result"]
                ):

                    image_data = base64.b64decode(
                        result["result"]["image"]
                    )

                    image = Image.open(
                        io.BytesIO(image_data)
                    ).convert("RGB")

                    print("✓ Image generated")

                    return image

                print("Invalid Cloudflare response.")

            elif response.status_code == QUOTA_STATUS_CODE:

                print(
                    f"{account['name']} quota exceeded."
                )

                continue

            else:

                print(
                    f"Status Code: {response.status_code}"
                )

                print(response.text)

        except Exception as exc:

            print(exc)

            continue

    print("\nAll Cloudflare accounts failed.")

    return None


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
        (22, 24, 30),
    )

    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (
            80,
            80,
            REEL_WIDTH - 80,
            REEL_HEIGHT - 80,
        ),
        outline=(90, 90, 90),
        width=3,
    )

    draw.text(
        (120, 140),
        "Image Generation Failed",
        fill=(240, 240, 240),
    )

    draw.text(
        (120, 240),
        scene[:200],
        fill=(180, 180, 180),
    )

    image.save(output)

    return str(output)

# ============================================================
# IMAGE PROCESSING
# ============================================================

def enhance_natural_clarity(
    image: Image.Image,
) -> Image.Image:

    """
    Apply a subtle finishing pass so generated images stay clear,
    naturally colored, and not hazy.
    """

    image = image.convert("RGB")

    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Color(image).enhance(1.04)
    image = ImageEnhance.Sharpness(image).enhance(1.12)

    image = image.filter(
        ImageFilter.UnsharpMask(
            radius=1.2,
            percent=80,
            threshold=3,
        )
    )

    return image


# ============================================================
# IMAGE PROCESSING
# ============================================================

def resize_for_reel(
    image: Image.Image,
) -> Image.Image:

    """
    Resize image for Instagram Reel.

    Keeps aspect ratio.

    Uses center crop.

    Never stretches.

    Final size:
    1080 x 1920
    """

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
# SINGLE IMAGE GENERATION
# ============================================================

def generate_single_image(
    scene: Dict[str, Any],
    output_path: str,
) -> str:

    scene_type = scene.get(
        "type",
        "environment",
    )

    scene_description = scene.get(
        "description",
        "",
    )

    print("\n" + "=" * 60)
    print("GENERATING IMAGE")
    print("=" * 60)

    print(f"Type : {scene_type}")
    print(f"Scene: {scene_description}")

    prompt = build_prompt(
        scene_type=scene_type,
        scene_description=scene_description,
    )

    image = generate_image_with_cloudflare(
        prompt
    )

    if image is None:

        print(
            "Using placeholder image..."
        )

        return create_placeholder_image(
            output_path,
            scene_description,
        )

    image = resize_for_reel(
        image
    )

    image = enhance_natural_clarity(
        image
    )

    return save_image(
        image,
        output_path,
    )


# ============================================================
# SCENE VARIETY HELPERS
# ============================================================

RELATIONSHIP_KEYWORDS = {
    "couple", "love", "lover", "relationship", "together", "holding hands",
    "boy and girl", "girl and boy", "husband", "wife", "partner", "date",
}

PERSON_KEYWORDS = {
    "person", "man", "woman", "boy", "girl", "child", "old man", "old woman",
    "father", "mother", "friend", "student", "traveler", "someone", "he ", "she ",
}

OBJECT_KEYWORDS = {
    "book", "letter", "tea", "coffee", "cup", "phone", "diary", "journal",
    "bicycle", "umbrella", "lantern", "chair", "window", "door", "flowers",
}

ARCHITECTURE_KEYWORDS = {
    "library", "cafe", "station", "train", "bridge", "cabin", "house",
    "room", "balcony", "street", "shop", "home", "kitchen",
}

NATURE_VARIATIONS = [
    "quiet lake with wildflowers in the foreground and soft mountains far away",
    "empty winding road after light rain with trees bending over it and clear reflections",
    "golden field under a wide evening sky with birds crossing the clouds",
    "moonlit river with gentle reflections and tall grass moving in wind",
    "old wooden dock beside calm water during blue hour",
    "clear forest path with soft sunlight passing through leaves and crisp visible details",
    "peaceful ocean shore with scattered stones and pale sunset light",
    "small hill covered with grass and flowers under moving clouds",
]

OBJECT_VARIATIONS = [
    "two warm cups of tea on a wooden table beside a rainy window",
    "an open book with dried flowers on old wood near soft window light",
    "a bicycle leaning near wildflowers on a quiet country road",
    "an umbrella resting near a puddle reflecting evening lamps",
    "old letters tied with thread beside a small candle and flowers",
]

ARCHITECTURE_VARIATIONS = [
    "quiet old library corner with tall shelves and warm window light",
    "rainy cafe window with reflections on glass and an empty chair",
    "empty train station platform during golden evening light",
    "small wooden cabin surrounded by trees under a soft sky",
    "old bridge over a calm river with flowers near the railing",
]

COUPLE_VARIATIONS = [
    "a boy and girl holding hands on a quiet nature path, small figures, natural colors, no close-up faces",
    "two small figures sharing an umbrella on a rainy road with warm street reflections",
    "a couple sitting quietly apart on a wooden dock beside a calm lake at sunset",
    "two people walking beside wildflowers under a wide soft sky, hands almost touching",
]


def _contains_any(text: str, keywords: set[str]) -> bool:
    lowered = f" {text.lower()} "
    return any(keyword in lowered for keyword in keywords)


def enhance_scene_for_variety(scene: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Add visual variety while keeping the generated story scene as the base.
    This avoids six similar frames of a person facing away.
    """
    description = str(scene.get("description", "") or "").strip()
    scene_type = str(scene.get("type", "environment") or "environment").lower()

    if _contains_any(description, RELATIONSHIP_KEYWORDS):
        scene_type = "couple"
    elif _contains_any(description, PERSON_KEYWORDS):
        scene_type = "person"
    elif _contains_any(description, OBJECT_KEYWORDS):
        scene_type = "object"
    elif _contains_any(description, ARCHITECTURE_KEYWORDS):
        scene_type = "architecture"
    elif scene_type not in {"couple", "person", "object", "architecture", "environment"}:
        scene_type = "environment"

    if not description:
        if index in {2, 5}:
            scene_type = "object"
            description = random.choice(OBJECT_VARIATIONS)
        elif index == 3:
            scene_type = "architecture"
            description = random.choice(ARCHITECTURE_VARIATIONS)
        elif index == 4:
            scene_type = "couple"
            description = random.choice(COUPLE_VARIATIONS)
        else:
            scene_type = "environment"
            description = random.choice(NATURE_VARIATIONS)

    if scene_type == "environment" and index in {2, 5}:
        description += f". Add a unique foreground detail: {random.choice(OBJECT_VARIATIONS)}."
    elif scene_type == "person":
        description += ". The person should not always face away; use a varied natural pose and keep them secondary to the environment."
    elif scene_type == "couple":
        description += ". Show emotional connection through simple body language like holding hands, walking together, or sitting quietly; keep nature as the main visual mood."

    description += ". Use natural colors, crisp details, clear air, no haze, no fog, no mist, no blur, aesthetic composition, and no text in the image."

    return {
        "type": scene_type,
        "description": description,
    }


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

    scenes = reel_json.get(
        "visual_scenes",
        []
    )

    if not scenes:

        scenes = reel_json.get(
            "scenes",
            []
        )

        scenes = [
            {
                "type": "environment",
                "description": scene,
            }
            for scene in scenes
        ]

    if not scenes:

        raise ValueError(
            "No visual scenes found."
        )

    print()
    print("=" * 70)
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
            output_dir
            /
            f"{prefix}_{index:02d}.png"
        )

        print()
        print("-" * 70)
        print(
            f"Scene {index}/{len(scenes)}"
        )
        print("-" * 70)

        image = generate_single_image(
            scene=scene,
            output_path=str(output_path),
        )

        generated_images.append(
            image
        )

    print()
    print("=" * 70)
    print("IMAGE GENERATION COMPLETE")
    print("=" * 70)

    return generated_images


# ============================================================
# LOAD REEL JSON
# ============================================================

def load_reel_json(
    json_path: str | Path,
) -> Dict[str, Any]:

    json_path = Path(json_path)

    if not json_path.exists():

        raise FileNotFoundError(
            json_path
        )

    with open(
        json_path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# FIND ALL GENERATED IMAGES
# ============================================================

def get_generated_images(
    image_directory: str | Path,
) -> List[str]:

    image_directory = Path(image_directory)

    if not image_directory.exists():

        return []

    images = sorted(

        image_directory.glob(
            "scene_*.png"
        )

    )

    return [

        str(image)

        for image in images

    ]

# ============================================================
# SCENE ENHANCEMENT
# ============================================================

PERSON_ENVIRONMENTS = [

    "standing alone on a quiet beach",

    "walking on an empty road",

    "sitting on a wooden dock",

    "standing on a mountain overlook",

    "walking through a clear forest with crisp visible trees",

    "standing beside a calm lake",

    "sitting on a lonely park bench",

    "walking through a flower field",

    "standing under a large tree",

    "looking toward the ocean",

    "standing on a cliff",

    "walking beside railway tracks",

    "standing near an old bridge",

    "standing under the evening sky",

    "walking through tall grass"

]


SCENERY_ENVIRONMENTS = [

    "quiet beach at sunset",

    "clear mountain landscape with crisp distant details",

    "empty forest trail",

    "moon over a calm lake",

    "clear quiet country road after rain",

    "old wooden pier",

    "field of wild flowers",

    "river flowing through rocks",

    "rainy city street",

    "wooden cabin in the forest",

    "golden wheat field",

    "snow covered path",

    "lighthouse near the ocean",

    "peaceful ocean waves",

    "dramatic clouds above mountains",

    "old library interior",

    "coffee shop window during rain",

    "quiet village road",

    "sunlight through trees",

    "birds flying across the sky"

]


def normalize_scene(
    scene: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:

    """
    Improves scene variety.

    Roughly:

    40% tiny human

    60% environment only

    """

    scene_type = scene.get(
        "type",
        "environment",
    )

    description = scene.get(
        "description",
        "",
    ).strip()


    if not description:

        if index % 3 == 0:

            description = random.choice(
                PERSON_ENVIRONMENTS
            )

            scene_type = "person"

        else:

            description = random.choice(
                SCENERY_ENVIRONMENTS
            )

            scene_type = "environment"


    if scene_type.lower() == "person":

        description += """

            The person is extremely small.

            The environment dominates the image.

            Wide cinematic landscape.

            Large empty sky.

            Professional establishing shot.

            """

    else:

        description += """

            No close human subject.

            Environment tells the story.

            Beautiful landscape.

            Large cinematic composition.

            Minimal.

            Peaceful.

            """

    return {

        "type": scene_type,

        "description": description,

    }


    # ============================================================
    # UPDATE IMAGE GENERATION LOOP
    # ============================================================

    # Replace the loop inside generate_images_for_reel()

    generated_images = []

    for index, scene in enumerate(
        scenes,
        start=1,
    ):

        scene = normalize_scene(
            scene,
            index,
        )

        output_path = (
            output_dir
            /
            f"{prefix}_{index:02d}.png"
        )

        print()
        print("-" * 70)
        print(f"Generating Scene {index}")
        print("-" * 70)

        image_path = generate_single_image(
            scene=scene,
            output_path=str(output_path),
        )

        generated_images.append(
            image_path
        )

    return generated_images


# ============================================================
# STANDALONE TEST
# ============================================================


if __name__ == "__main__":


    import sys



    print("\n")
    print("=" * 60)
    print("AESTHETIC VIBES IMAGE TEST")
    print("=" * 60)



    # Change this path for testing

    TEST_JSON = (

        "/Users/priyom_saha/Documents/"
        "QuotesGenerator/Reels/"
        "output/20260802_153536/story.json"

    )



    try:


        reel_data = load_reel_json(

            TEST_JSON

        )



        print("\nQuote:")

        print(

            reel_data.get(

                "quote",

                "No quote"

            )

        )



        timestamp_folder = (

            Path(TEST_JSON)

            .parent

        )



        image_folder = (

            timestamp_folder

            /

            "images"

        )



        images = generate_images_for_reel(

            reel_json=reel_data,

            output_dir=image_folder,

            prefix="scene"

        )



        print("\n")
        print("=" * 60)
        print("GENERATION COMPLETE")
        print("=" * 60)



        for index, img in enumerate(

            images,

            start=1

        ):

            print(

                f"{index}. {img}"

            )



    except Exception as exc:


        print("\nERROR:")

        print(exc)



        import traceback


        traceback.print_exc()
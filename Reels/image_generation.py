"""
image_generation.py

Aesthetic Vibes Image Generator

Creates cinematic hand-drawn editorial illustrations
for short wisdom reels.

Visual Identity

✓ Environment-first composition
✓ Tiny human silhouette
✓ Dark blue/orange color palette
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

import requests
from PIL import Image, ImageDraw

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

Soft watercolor washes.

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

Deep navy blue.

Charcoal.

Muted teal.

Burnt orange.

Warm amber.

Dusty brown.

Soft grey.

Muted cream highlights.

Low saturation.

Dark cinematic color grading.

Blue hour.

Golden hour.

Late sunset.

Soft moonlight.

Foggy morning.

Deep natural shadows.

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

Foggy road.

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

Mist.

Fog.

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

    # Determine if person should be included
    include_person = scene_type.lower() == "person" and "person" in scene_description.lower()
    
    person_instruction = ""
    if include_person:
        person_instruction = "ONE tiny person (equal mix of male/female figures, vary naturally) as small distant silhouette (max 5%), back/side view, simple action. Logical context - sitting on bench/rock, walking on path, standing on cliff."
    else:
        person_instruction = "Pure nature scene, no people. Focus on landscape."
    
    # Choose color palette based on mode
    if USE_BRAND_COLORS:
        color_instruction = """BRAND COLORS (MANDATORY): Bright pink (#FF2075) in sky/lights/highlights, dark burgundy (#610B2D) shadows, navy blue depth, muted cream accents. Pink-tinted atmosphere - pink sunset, pink mist, purple night, burgundy shadows. Color grade entire scene pink/purple/blue. NEVER: bright green, yellow, orange."""
    else:
        color_instruction = """Colors: Navy blue, charcoal, muted teal, burnt orange, warm amber, cream. Low saturation, moody cinematic grading."""
    
    return f"""
Hand-drawn sketch illustration. Loose linework, soft watercolor, paper texture. Impressionistic editorial style.

Scene: {scene_description}

{person_instruction}

Nature: rain clouds, mist, fog, moonlight, stars, birds, waves, wind, grass, trees, flowers, water reflections.

Composition: Extreme wide shot. 90-95% landscape. Huge empty sky/water. Rule of thirds. Space for text.

Atmosphere: Calm, peaceful, melancholic, quiet, reflective, minimal. Blue hour, golden hour lighting.

{color_instruction}

Style: Artistic sketch, loose strokes, simplified forms, elegant minimalism. Abstract faces if visible.
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

    "walking through a foggy forest",

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

    "misty mountain landscape",

    "empty forest trail",

    "moon over a calm lake",

    "foggy country road",

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
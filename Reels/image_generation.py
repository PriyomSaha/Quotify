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

CF_ACCOUNT_ID_3 = os.getenv("CF_ACCOUNT_ID_3")
CF_TOKEN_3 = os.getenv("CF_TOKEN_3")

CF_ACCOUNT_ID_4 = os.getenv("CF_ACCOUNT_ID_4")
CF_TOKEN_4 = os.getenv("CF_TOKEN_4")

CF_ACCOUNT_ID_5 = os.getenv("CF_ACCOUNT_ID_5")
CF_TOKEN_5 = os.getenv("CF_TOKEN_5")

CF_ACCOUNT_ID_6 = os.getenv("CF_ACCOUNT_ID_6")
CF_TOKEN_6 = os.getenv("CF_TOKEN_6")

CF_ACCOUNT_ID_7 = os.getenv("CF_ACCOUNT_ID_7")
CF_TOKEN_7 = os.getenv("CF_TOKEN_7")

CF_ACCOUNT_ID_8 = os.getenv("CF_ACCOUNT_ID_8")
CF_TOKEN_8 = os.getenv("CF_TOKEN_8")

# CF_MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
CF_MODEL = "@cf/leonardo/lucid-origin"

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
    {
        "name": "Secondary 1",
        "account_id": CF_ACCOUNT_ID_3,
        "api_token": CF_TOKEN_3,
    },
    {
        "name": "Account 4",
        "account_id": CF_ACCOUNT_ID_4,
        "api_token": CF_TOKEN_4,
    },
    {
        "name": "Account 5",
        "account_id": CF_ACCOUNT_ID_5,
        "api_token": CF_TOKEN_5,
    },
    {
        "name": "Account 6",
        "account_id": CF_ACCOUNT_ID_6,
        "api_token": CF_TOKEN_6,
    },
    {
        "name": "Account 7",
        "account_id": CF_ACCOUNT_ID_7,
        "api_token": CF_TOKEN_7,
    },
    {
        "name": "Account 8",
        "account_id": CF_ACCOUNT_ID_8,
        "api_token": CF_TOKEN_8,
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

# BASE_STYLE_PROMPT = """
# Create a beautiful cinematic digital painting.
# Clean, culturally specific, and symbol-driven visual storytelling.
# Painterly brush strokes.
# Soft natural textures.
# Natural atmospheric lighting that matches the scene.
# Rich but realistic colors.
# Emotional storytelling through iconic symbols, places, atmosphere, and meaningful national or cultural context.
# Premium cinematic composition.
# Highly detailed environment.
# Natural perspective.
# Award-winning illustration.
# Movie still.
# Professional composition.
# Vertical 9:16.
# No text.
# """

# STYLE_VARIATIONS = [
#     "Japanese slice-of-life anime film look, hand-painted background art, peaceful everyday emotion.",
#     "Cinematic painterly editorial illustration, natural textures, grounded emotional realism.",
#     "Dreamy animated movie background style, lush plants, soft clouds, warm nostalgic color palette.",
#     "Watercolor-like painterly illustration, quiet poetic atmosphere, delicate light and shadow.",
#     "Soft Ghibli-style animated film mood, hand-painted backgrounds, whimsical nature, gentle character design.",
#     "Soft aesthetic film style, pastel palette, gentle haze, dreamy nostalgic mood, minimalist composition.",
#     "Hand-painted 2D watercolor illustration, delicate linework, warm nostalgic mood, rich natural colors.",
# ]

BASE_STYLE_PROMPT = """
        Create a cinematic 2D animated-film frame.
        Graphic cel-shaded illustration with bold dark ink outlines.
        Flat layered color blocks and simplified posterized shadows.
        Natural cinematic composition and believable perspective.
        Muted vintage color grading with strong atmospheric contrast.
        Detailed environments with simplified hand-drawn forms.
        Subtle analog film grain and screen-print texture.
        Expressive but understated characters.
        Cinematic lighting and deep environmental atmosphere.
        Looks like a still from a mature Japanese animated film.
        Vertical 9:16.
        No text.
    """

STYLE_VARIATIONS = [
    "Cinematic 2D cel-shaded animation, bold ink outlines, muted colors, posterized shadows, subtle film grain.",
    "Japanese 2D anime frame, graphic linework, flat color blocks, muted vintage tones, analog grain.",
    "Cinematic 2D illustration, strong dark outlines, simplified shading, earthy colors, textured film grain.",
    "Mature anime film aesthetic, cel-shaded forms, graphic outlines, subdued colors, atmospheric grain.",
    "Vintage 2D animation frame, bold linework, flat layered colors, cinematic shadows, subtle print texture.",
    "Cinematic animated-film style, clean ink contours, posterized lighting, muted palette, analog film texture.",
    "Japanese 2D film illustration, graphic shadows, dark outlines, restrained colors, nostalgic grain texture.",
    "Stylized cinematic 2D animation, crisp outlines, simplified shading, vintage color grade, subtle film grain."
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
collage,
multiple panels,
comic panels,
multi-panel,
grid layout,
split-screen,
storyboard,
mosaic of images,
frame borders,
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
generic apartment balcony for no reason,
watercolor,
oil painting,
soft watercolor wash,
photorealistic,
3d render,
glossy digital art,
realistic skin texture,
hyperrealism,
close-up,
extreme close-up,
medium close-up,
portrait,
portrait framing,
face close-up,
headshot,
facial close-up,
zoomed-in composition,
tight framing,
tight crop,
subject filling the frame,
face dominating the frame,
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

# Maximum prompt length for @cf/stabilityai/stable-diffusion-xl-base-1.0
# on Cloudflare Workers AI. This matches the model's hard limit of 2048
# characters. Prompts are always kept within this bound; compact_prompt's
# word-boundary-safe truncation is a safety net only for edge cases.
MAX_PROMPT_LENGTH = 2048


def normalize_prompt_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact_prompt(text: str) -> str:
    text = normalize_prompt_text(text)
    if len(text) > MAX_PROMPT_LENGTH:
        text = text[:MAX_PROMPT_LENGTH].rstrip()
        # Cut at a word boundary instead of mid-word.
        last_space = text.rfind(" ")
        if last_space > int(MAX_PROMPT_LENGTH * 0.5):
            text = text[:last_space].rstrip()
    return text


# ============================================================
# STORY-AWARE SCENE ANALYSIS
# ============================================================
# The scene description is the SOURCE OF TRUTH for what the image
# must contain. The resolvers below only ADD variation for aspects
# the story does NOT already specify, and every random choice is
# constrained so it can never contradict the story's location,
# weather, season, time, mood or objects.


def _kw_matches(text: str, keywords: List[str]) -> bool:
    """True when any keyword appears in text.

    Single words use word boundaries ('sea' never matches 'search'),
    multi-word phrases use plain substring matching ('rainy city
    street' still matches "rainy city street with soft reflections").
    """
    lowered = (text or "").lower()
    for kw in keywords:
        if " " in kw:
            if kw in lowered:
                return True
        elif re.search(rf"\b{re.escape(kw)}\b", lowered):
            return True
    return False


def _matched_labels(text: str, label_groups) -> List[str]:
    """Return labels whose keywords appear in text.

    ``label_groups`` is priority-ordered: the first matching group is
    the one that must win, so a literal environment in the story
    (beach, train, field...) always beats a generic word.
    """
    return [
        label
        for label, keywords in label_groups
        if _kw_matches(text, keywords)
    ]


# --- Environment groups (priority ordered: most specific wins) ---
ENVIRONMENT_GROUPS = [
    ("coastal / beach", ["beach", "ocean", "sea", "seafront", "seashore",
                         "seaside", "coast", "shore", "waves", "sand",
                         "cliff"]),
    ("train", ["train", "railway", "rail track", "platform", "metro",
               "compartment", "carriage"]),
    ("bus", ["bus", "bus stop", "bus window"]),
    ("mountain", ["mountain", "mountains", "hill", "hills", "slope",
                  "peak", "ridge"]),
    ("forest", ["forest", "pine", "woodland", "woods", "jungle",
                "trees", "thicket"]),
    ("field / meadow", ["field", "meadow", "grassland", "wheat",
                        "pasture"]),
    ("river / lake", ["river", "lake", "pond", "stream", "canal"]),
    ("desert", ["desert", "dunes"]),
    ("school / classroom", ["classroom", "school", "college"]),
    ("library", ["library"]),
    ("coffee / cafe", ["coffee", "cafe", "café"]),
    ("tea stall", ["tea", "chai"]),
    ("rooftop", ["rooftop", "roof"]),
    ("balcony", ["balcony"]),
    ("bridge", ["bridge"]),
    ("station", ["station"]),
    ("airport / travel", ["airport", "flight", "plane"]),
    ("village / countryside", ["village", "countryside", "rural"]),
    ("park / garden", ["park", "garden"]),
    ("room / home / interior", ["room", "house", "home", "apartment",
                                "bedroom", "living room", "kitchen",
                                "hall", "interior", "cabin", "veranda",
                                "window", "doorway"]),
    ("city / street", ["city", "urban", "street", "road", "avenue",
                       "alley", "lane", "market"]),
]

ENVIRONMENT_PHRASES = {
    "coastal / beach": "coastal ocean beach with sand, waves and shoreline",
    "train": "train / railway setting - platform or compartment interior",
    "bus": "bus / bus stop setting",
    "mountain": "mountain setting with slopes and distant peaks",
    "forest": "forest / woodland setting with trees",
    "field / meadow": "open field / meadow setting",
    "river / lake": "river / lake / water body setting",
    "desert": "desert setting with dry sand",
    "school / classroom": "classroom / school setting",
    "library": "library / reading room setting",
    "coffee / cafe": "coffee shop / cafe setting",
    "tea stall": "tea stall / chai shop setting",
    "rooftop": "rooftop setting",
    "balcony": "balcony setting",
    "bridge": "bridge / crossing setting",
    "station": "public transport station / platform setting",
    "airport / travel": "airport / travel terminal setting",
    "village / countryside": "village / countryside setting",
    "park / garden": "park / garden setting",
    "room / home / interior": "indoor room / home / interior space",
    "city / street": "city street / urban road setting",
}

# --- Weather groups (priority: rain > snow > fog > cloudy > sunny > wind) ---
WEATHER_GROUPS = [
    ("rain", ["rain", "rainy", "raining", "monsoon", "drizzle", "downpour",
              "shower", "wet", "puddle", "puddles", "stormy", "storm",
              "rainfall", "raindrop", "raindrops"]),
    ("snow", ["snow", "snowy", "snowing", "snowfall", "frost", "frosty",
              "ice", "icy", "sleet"]),
    ("fog", ["fog", "foggy", "mist", "misty", "haze", "hazy"]),
    ("cloudy", ["cloudy", "cloud", "clouds", "overcast"]),
    ("sunny", ["sunny", "sunshine", "sunlit", "sunlight", "clear sky",
               "bright"]),
    ("windy", ["wind", "winds", "windy", "breeze", "gust", "gusty"]),
]

WEATHER_PHRASES = {
    "rain": "rain / wet surfaces with puddles and reflective shine",
    "snow": "snow / snowfall with snow building up on the ground",
    "fog": "fog / mist softly wrapping the scene",
    "cloudy": "cloudy / overcast sky",
    "sunny": "sunny and bright with strong daylight",
    "windy": "windy with visible air movement",
}

# --- Time of day groups (priority: night > dawn > morning > afternoon > sunset) ---
TIME_GROUPS = [
    ("night", ["night", "midnight", "moon", "moonlit", "moonlight",
               "stars", "starry", "dark"]),
    ("dawn", ["dawn", "sunrise", "daybreak", "first light"]),
    ("morning", ["morning"]),
    ("afternoon", ["noon", "afternoon", "midday"]),
    ("sunset / dusk", ["sunset", "dusk", "twilight", "evening",
                       "golden hour"]),
]

TIME_PHRASES = {
    "night": "night / after dark",
    "dawn": "dawn / sunrise",
    "morning": "morning",
    "afternoon": "afternoon / midday",
    "sunset / dusk": "sunset / dusk / evening",
}

# --- Season groups ---
SEASON_GROUPS = [
    ("summer", ["summer"]),
    ("winter", ["winter", "wintry"]),
    ("spring", ["spring", "blossom"]),
    ("autumn", ["autumn", "fallen leaves", "falling leaves"]),
    ("monsoon", ["monsoon"]),
]

SEASON_PHRASES = {
    "summer": "summer",
    "winter": "winter",
    "spring": "spring",
    "autumn": "autumn / fall",
    "monsoon": "monsoon / rainy season",
}

def _normalize_weather_labels(
    story_labels: List[str],
    time_labels: List[str],
    season_labels: List[str],
) -> List[str]:
    """Keep the story's weather words but drop impossible combos."""
    labels = [label for label in story_labels]
    if "sunny" in labels and (
        "night" in time_labels
        or "rain" in labels
        or "snow" in labels
        or "winter" in season_labels
        or "monsoon" in season_labels
    ):
        labels.remove("sunny")
    return labels


def _fallback_weather_label(
    time_labels: List[str],
    season_labels: List[str],
    env_labels: List[str],
) -> str:
    """Story never mentions weather -> invent one that still fits the
    story's time, season and location clues. Never a contradiction."""
    if "monsoon" in season_labels:
        return "rain"
    if "winter" in season_labels:
        return "snow"
    banned = set()
    if "night" in time_labels:
        banned.add("sunny")
    if any(label in env_labels for label in ("coastal / beach", "desert")):
        banned.add("snow")
    if "summer" in season_labels:
        banned.add("snow")
    choices = [label for label in WEATHER_PHRASES if label not in banned]
    if not choices:
        choices = list(WEATHER_PHRASES)
    return random.choice(choices)


def _resolve_environment(
    text: str,
    env_labels: List[str],
    weather_labels: List[str],
    time_labels: List[str],
) -> str:
    """Environment must come from the story. We only randomise it when
    the story does not specify any location, and even then the choice
    stays compatible with the story's weather / time."""
    if env_labels:
        label = env_labels[0]
        return (
            f"{ENVIRONMENT_PHRASES[label]} (the story's exact location - "
            "do not replace it with any other place)"
        )
    if "rain" in weather_labels:
        pool = [
            "rainy city street with soft reflections",
            "empty countryside road after rain",
            "forest trail with wet leaves",
            "village street after monsoon rain",
            "quiet bus stop after rainfall",
        ]
    elif "snow" in weather_labels:
        pool = ["snow covered path through trees"]
    elif "fog" in weather_labels:
        pool = ["misty pine forest", "fog-bathed river bank"]
    elif "night" in time_labels:
        pool = ["moonlit lake with gentle ripples",
                "lighthouse during blue hour",
                "quiet street under a starry night sky"]
    else:
        pool = ENVIRONMENTS
    return random.choice(pool)


def _resolve_weather(weather_labels: List[str]) -> str:
    return "; ".join(WEATHER_PHRASES[label] for label in weather_labels)


def _resolve_time(time_labels: List[str], weather_labels: List[str]) -> str:
    if time_labels:
        return " and ".join(TIME_PHRASES[label] for label in time_labels)
    # Story never fixes the clock -> randomise, but a bright sunny/clear
    # sky can never land on "night".
    if "sunny" in weather_labels or "cloudy" in weather_labels:
        options = ["dawn", "morning", "afternoon", "sunset / dusk"]
    else:
        options = ["dawn", "morning", "afternoon", "sunset / dusk", "night"]
    return TIME_PHRASES[random.choice(options)]


def _resolve_season(season_labels: List[str],
                    weather_labels: List[str]) -> str:
    if season_labels:
        return " and ".join(SEASON_PHRASES[label] for label in season_labels)
    if "snow" in weather_labels:
        return "winter"
    if "rain" in weather_labels:
        return "monsoon / rainy season"
    if "sunny" in weather_labels or "cloudy" in weather_labels:
        return random.choice(["summer", "spring", "autumn"])
    return random.choice(["summer", "winter", "spring", "autumn"])


def _resolve_lighting(weather_labels: List[str],
                      time_labels: List[str]) -> str:
    lights = []
    if "night" in time_labels:
        lights.append("moonlit / blue-hour ambient light")
    if "dawn" in time_labels:
        lights.append("soft purple-pink dawn glow")
    if "morning" in time_labels:
        lights.append("warm low-angled morning light")
    if "afternoon" in time_labels:
        lights.append("bright natural daylight")
    if "sunset / dusk" in time_labels:
        lights.append("golden-hour glow")
    if "rain" in weather_labels:
        lights.append("soft overcast rain light with wet sheen")
    if "snow" in weather_labels:
        lights.append("cold diffused snowy light")
    if "fog" in weather_labels:
        lights.append("soft hazy diffused light")
    if "cloudy" in weather_labels:
        lights.append("even, muted overcast light")
    if "sunny" in weather_labels:
        lights.append("bright sunlit light")
    if not lights:
        lights = [random.choice(LIGHTING)]
    return ", ".join(dict.fromkeys(lights))

MOOD_SIGNAL_WORDS = [
    "peaceful", "nostalgic", "melancholic", "hopeful", "quiet",
    "reflective", "comforting", "dreamlike", "calm", "lonely",
    "sorrowful", "tender", "joyful", "sad", "eerie", "tense",
    "yearning", "longing",
]


def _resolve_mood(text: str,
                  weather_labels: List[str],
                  time_labels: List[str]) -> str:
    lowered = (text or "").lower()
    matched = [word for word in MOOD_SIGNAL_WORDS if word in lowered]
    if matched:
        return ", ".join(matched[:2])
    if "rain" in weather_labels:
        return "quiet, introspective"
    if "snow" in weather_labels:
        return "still, peaceful"
    if "fog" in weather_labels:
        return "mysterious, muted"
    if "night" in time_labels:
        return "introspective, calm"
    return random.choice(MOODS)


# --- Story-relevant foreground objects -------------------------------------
FOREGROUND_STORY_OBJECTS = [
    "umbrella", "rain puddles", "puddles", "puddle", "book", "books",
    "letter", "diary", "tea cup", "teacup", "coffee cup", "lantern",
    "curtain", "photo frame", "bus ticket", "window", "notebook", "lamp",
    "flowers", "shell", "shells", "bicycle", "old bicycle", "wildflowers",
    "fallen leaves", "leaves", "grass", "balcony plants", "paper letter",
]


def _resolve_foreground(text: str,
                        env_labels: List[str],
                        weather_labels: List[str],
                        time_labels: List[str]) -> str:
    """Foreground objects must come from the story or be compatible with
    its detected environment / weather. Never randomly adds cars,
    bicycles, flowers, umbrellas, books, etc."""
    lowered = (text or "").lower()
    matched = [obj for obj in FOREGROUND_STORY_OBJECTS if obj in lowered]
    if matched:
        return (
            ", ".join(matched)
            + " - these objects are specifically from the story; render "
            "them exactly as described and do NOT add random extras."
        )
    if "rain" in weather_labels:
        return ("story-compatible foreground: rain puddles, wet reflective "
                "surfaces and faint rain streaks")
    if "snow" in weather_labels:
        return ("story-compatible foreground: a fresh layer of snow on the "
                "nearest surfaces")
    if "fog" in weather_labels:
        return "soft foreground fog gently blurring the nearest shapes"
    if "night" in time_labels:
        return ("quiet pool of warm lamplight in the foreground "
                "(no unrelated objects)")
    if "coastal / beach" in env_labels:
        return "foreground: wet sand, rolling wave-foam and a few seashells"
    if "train" in env_labels:
        return "foreground: train window, seat back and handrail near the viewer"
    if "bus" in env_labels:
        return "foreground: bus window and handrail close to the viewer"
    if "room / home / interior" in env_labels or "balcony" in env_labels:
        return ("foreground: indoor objects only if the story mentions them "
                "(e.g. window light, a mug) - nothing random")
    if "forest" in env_labels:
        return "foreground: moss-covered rocks, ferns and wet leaves underfoot"
    if "mountain" in env_labels:
        return "foreground: rocky terrain and dark evergreen silhouettes"
    if "river / lake" in env_labels:
        return "foreground: smooth water with a stone or leaf on the bank"
    if "field / meadow" in env_labels:
        return "foreground: tall grass and wildflowers bending in the wind"
    if "city / street" in env_labels:
        return "foreground: a clean lamp-lit street surface (no unrelated vehicles)"
    return ("foreground details only if the story mentions them - no random "
            "vehicles, bicycles, flowers, books, umbrellas or other unrelated "
            "objects")


# --- Story-aware negative prompt -------------------------------------------
# Negative-prompt fragments that would fight the story when the story
# explicitly requires the same element. Format: (fragment found inside
# NEGATIVE_PROMPT, story keywords that make keeping the fragment harmful).
NEGATIVE_STORY_CONFLICTS = [
    ("cozy home interior", ["home", "house", "room", "apartment", "interior",
                            "bedroom", "kitchen", "hall"]),
    ("cozy family room", ["room", "home", "family"]),
    ("small wooden cabin", ["cabin"]),
    ("house exterior", ["house", "cabin", "home", "bungalow"]),
    ("bungalow", ["bungalow", "house", "home"]),
    ("balcony", ["balcony", "rooftop", "apartment"]),
    ("window-view apartment", ["window", "apartment", "room"]),
    ("tea stall", ["tea", "tea cup", "chai"]),
    ("coffee shop", ["coffee", "cafe", "café"]),
    ("old city lane", ["city", "street", "lane", "alley", "road", "market"]),
    ("rainy street", ["rain", "rainy", "monsoon", "wet", "street",
                      "puddle", "puddles"]),
    ("apartment balcony", ["balcony", "apartment", "rooftop"]),
]


def build_normal_day_negative_prompt(scene_description: str) -> str:
    """Base negative prompt minus any item that would contradict an
    element the story explicitly requires to be SHOWN."""
    desc = (scene_description or "").lower()
    kept = []
    for part in NEGATIVE_PROMPT.split(","):
        item = part.strip()
        if not item:
            continue
        should_drop = any(
            fragment in item.lower()
            and any(seed in desc for seed in story_seeds)
            for fragment, story_seeds in NEGATIVE_STORY_CONFLICTS
        )
        if not should_drop:
            kept.append(item)
    return compact_prompt(", ".join(kept))


# ============================================================
# STORY-AWARE SCENE ANALYSIS
# ============================================================

def build_style_prompt(
    event_mode: bool = False,
    style_variation: Optional[str] = None,
) -> str:
    """Return a compact style directive.

    Normal days AND event-based days use the SAME artistic style variation
    (the 2D cel-shaded anime look + a strict SINGLE-FRAME rule) so normal
    reels and event-based reels stay visually consistent. The event-specific
    look for event-based reels is driven entirely by the SCENE FOCUS
    (EVENT IMAGE FOCUS) block added by ``build_prompt``, NOT by a different
    artistic style.

    Keep it short: it is the first block of every prompt and Cloudflare
    caps prompts at 2048 characters.
    """
    variation = style_variation or STYLE_VARIATIONS[0]
    base = (
        f"{variation}. "
        "2D cinematic anime frame, one full-bleed shot covering the entire "
        "canvas - a single continuous scene. "
        "No collage, no panels, no grid, no storyboard, no split screen."
    )

    if event_mode:
        # Same style variation as normal mode. Only add an event-first
        # identity reminder so event scenes still clearly read as the
        # occasion without introducing a different artistic style.
        return (
            base + " "
            "Event-first visual identity: the scene must clearly read as the "
            "named occasion through its iconic symbols and cultural elements, "
            "while keeping the cel-shaded 2D anime style above."
        )

    return base


def build_prompt(
    scene_type: str,
    scene_description: str,
    event_instruction: Optional[str] = None,
) -> str:
    """Build the normal-day image prompt.

    The scene description is the source of truth. Environment, weather,
    season, time of day, lighting, mood and foreground are only
    randomised when the story does NOT specify them, and even then the
    random choices are constrained so they never contradict the story.

    When ``event_instruction`` is provided (event-based reels), the SAME
    style variation as normal mode is reused (see ``build_style_prompt``)
    and an ``EVENT IMAGE FOCUS`` block is appended so the scene clearly
    reads as the active occasion. The artistic style itself never diverges
    from the normal-day cel-shaded look.
    """
    scene_type = (scene_type or "environment").lower().strip()
    scene_description = (scene_description or "").strip()   

    if scene_type == "couple":
        subject = (
            "Two clearly visible people are central to the scene."
            "Natural interaction and body language expressing the emotional story. "
            "Walking together, sitting quietly, holding hands, sharing an umbrella or enjoying a peaceful moment."
            "No close-up faces."
        )

    elif scene_type == "person":
        subject = (
            "One visible person interacts naturally with the environment. "
            "The person is secondary to the overall environment and occupies only "
            "a small portion of the frame. Full body visible from head to feet. "
            "Distant or long-shot scale. Natural body language expressing the story. "
            "Never a portrait, never a close-up, never a selfie."
        )

    elif scene_type == "object":
        subject = (
            "The story's specified object is visible within its surrounding environment. "
            "The object must not become a close-up subject. "
            "Show the object at natural scale within a wide environmental composition. "
            "Include a visible person interacting naturally with it when appropriate. "
            "The surrounding location remains clearly visible."
        )

    elif scene_type == "architecture":
        subject = (
            "The location and surrounding environment are the main visual subject. "
            "Show the complete architectural/environmental setting in a wide shot. "
            "Only include people if the story explicitly requires them. "
            "Any person must remain small and naturally integrated into the environment. "
            "Never use portrait framing."
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
            "A person is present in the room, naturally interacting with the objects and environment."
        )

    elif scene_type == "abstract_emotion":
        subject = (
            "Emotion is communicated through the environment, light, space, "
            "shadow, weather, architecture, roads, water, windows and empty spaces. "
            "Show one visible person interacting naturally with the environment. "
            "The person is small within the frame and never the dominant subject. "
            "Use a distant environmental composition, not a portrait."
        )

    else:
        subject = (
            "Environment is the main subject."
            "Include 1–2 human characters as the emotional focus of the scene."
            "Nature tells the story through forests, rivers, fields, sky, rain, wind, flowers, stones, clouds, moonlight, and soft natural movement. "
            "Full-body or medium-distance composition, not a portrait."
        )

    # ---- Story-aware scene breakdown ----
    # The scene description is the SOURCE OF TRUTH. The resolvers below
    # only randomise aspects the story does NOT specify, and their random
    # picks are constrained so they can never contradict the story.
    env_labels = _matched_labels(scene_description, ENVIRONMENT_GROUPS)
    story_weather_labels = _matched_labels(scene_description, WEATHER_GROUPS)
    time_labels = _matched_labels(scene_description, TIME_GROUPS)
    season_labels = _matched_labels(scene_description, SEASON_GROUPS)

    weather_labels = _normalize_weather_labels(
        story_weather_labels,
        time_labels,
        season_labels,
    )
    if not weather_labels:
        weather_labels = [
            _fallback_weather_label(
                time_labels,
                season_labels,
                env_labels,
            )
        ]

    environment = _resolve_environment(
        scene_description,
        env_labels,
        weather_labels,
        time_labels,
    )
    weather = _resolve_weather(weather_labels)
    time_phrase = _resolve_time(time_labels, weather_labels)
    season_phrase = _resolve_season(season_labels, weather_labels)
    lighting = _resolve_lighting(weather_labels, time_labels)
    mood = _resolve_mood(scene_description, weather_labels, time_labels)
    foreground = _resolve_foreground(
        scene_description,
        env_labels,
        weather_labels,
        time_labels,
    )

    variation = cinematic_variation()

    event_focus_block = (
        ""
        if not event_instruction
        else (
            "EVENT IMAGE FOCUS (event-based reels):\n"
            f"{event_instruction}\n"
        )
    )

    prompt = f"""STYLE:
{build_style_prompt(event_mode=bool(event_instruction))}
This fixed style only controls HOW it is drawn; it never changes WHAT is shown.

STORY / SCENE (SOURCE OF TRUTH):
{scene_description}
{event_focus_block}
CHARACTER + ACTION:
{subject}

ENVIRONMENT:
{environment}

WEATHER / SEASON / TIME:
Weather: {weather}; Season: {season_phrase}; Time: {time_phrase}.
Lighting: {lighting}; Mood: {mood}.

FOREGROUND DETAILS:
{foreground}

CINEMATIC COMPOSITION:
Vertical 9:16, one continuous full-bleed shot.
{variation['camera']}, {variation['lens']}.
Environment-dominant composition.
The camera is physically far from the subject.
Show the entire surrounding environment clearly.
If a person is present, show the complete body at a small-to-medium scale,
never a face close-up or portrait.
The environment must occupy most of the frame.
Use strong foreground, middle-ground and background depth.
Do not crop the person or important environmental objects.
No close-up, no medium close-up, no portrait framing.
Full scene visible from a natural cinematic distance.
Detailed, sharp, cinematic movie still.

STORY FIDELITY:
The scene description is the source of truth. Do not contradict or replace
its location, weather, season, time, activity, objects, relationships, or
actions. Do not introduce unrelated vehicles, objects, animals, buildings,
or environments.

NO TEXT:
No text, letters, captions, logos, watermarks, signatures, frames or borders.
"""

    return compact_prompt(prompt)

# ============================================================
# CLOUDFLARE IMAGE GENERATION
# ============================================================

def generate_image_with_cloudflare(
    prompt: str,
    event_mode: bool = False,
    negative_prompt_override: Optional[str] = None,
) -> Optional[Image.Image]:
    prompt = compact_prompt(prompt)
    negative_prompt = compact_prompt(NEGATIVE_PROMPT)

    if event_mode:
        steps = 8
        guidance = 10
        negative_prompt = compact_prompt(
            NEGATIVE_PROMPT
            + ", random people, random cars, random vehicles, random objects, random animals, "
            + "generic home scene, balcony with plants, cabin, bungalow, cozy room, rainy city street, "
            + "tea stall, coffee shop, apartment interior, abstract vague imagery, unclear composition, "
            + "unrelated subject matter, off-topic content, random lady, random man, random woman, "
            + "random child, random stranger, random face, random portrait, low resolution, poorly rendered"
        )
    else:
        steps = random.choice([15, 20])
        guidance = random.choice([7.0, 7.5, 8.0, 8.5])
        if negative_prompt_override:
            # For normal days the negative prompt is built from the actual
            # scene description so it never suppresses an element the story
            # explicitly requires (rain, coffee shop, tea stall, balcony...).
            negative_prompt = compact_prompt(negative_prompt_override)

    # Cloudflare Workers AI stable-diffusion-xl-base-1.0 expects ``num_steps``
    # (not ``steps``) and accepts an explicit canvas size. Rendering a real
    # 9:16 portrait canvas up front stops the model from "tiling" the default
    # square 1024x1024 output into collage-like stacked panels when asked for
    # a vertical composition.
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "num_steps": steps,
        "guidance": guidance,
        "width": 768,
        "height": 1344,
        "seed": random.randint(0, 2**32 - 1),
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

        # if response.status_code != 200:
        #     print(f"HTTP {response.status_code}")

        #     try:
        #         print(response.json())
        #     except Exception:
        #         print(response.text)

        #     continue

        # try:
        #     # New Cloudflare model returns the actual PNG binary,
        #     # not JSON containing a Base64 image.
        #     image = Image.open(
        #         io.BytesIO(response.content)
        #     ).convert("RGB")

        #     print("✓ Image generated successfully")

        #     return image

        # except Exception as exc:
        #     print(f"Image Decode Error: {exc}")
        #     continue

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

    # The event / special-date branch was removed when the pipeline became
    # normal-day only. Scene type detection and the empty-description
    # fallback above are enough here.
    # (No random lighting/mood/foreground text is appended - that used to
    # contradict the story. All variation is applied inside build_prompt(),
    # which is story-aware.)

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
) -> str:
    scene_type = scene.get("type", "environment")
    scene_description = scene.get("description", "").strip()

    print("\n" + "=" * 60)
    print("GENERATING IMAGE")
    print("=" * 60)
    print(f"Type : {scene_type}")
    print(f"Scene: {scene_description}")
    if event_instruction:
        print(f"Event focus: {event_instruction[:160]}")

    prompt = build_prompt(
        scene_type=scene_type,
        scene_description=scene_description,
        event_instruction=event_instruction,
    )

    if event_instruction:
        # Event-based images reuse the SAME style variation as normal mode
        # (cel-shaded 2D anime — see build_prompt/build_style_prompt). Only the
        # Cloudflare negative prompt / guidance tightens to avoid generic
        # scenes — see generate_image_with_cloudflare(event_mode=True).
        image = generate_image_with_cloudflare(prompt, event_mode=True)
    else:
        normal_negative = build_normal_day_negative_prompt(scene_description)
        image = generate_image_with_cloudflare(
            prompt,
            event_mode=False,
            negative_prompt_override=normal_negative,
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

    # Event-aware image generation. When an event is active, each scene is
    # given an EVENT IMAGE FOCUS instruction so it clearly reads as the
    # occasion. The artistic STYLE is unchanged — event-based images use the
    # SAME style variation (cel-shaded 2D anime) as normal mode; only the
    # per-scene visual focus differs.
    from event_detector import CONTENT_REEL, build_event_image_instruction, get_today_event

    event = get_today_event(content_type=CONTENT_REEL)
    if event:
        print(
            f"Event active: {event.get('name', 'special occasion')} — "
            "event-based images use the SAME style variation as normal mode"
        )

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

        # Per-scene event visual identity (deterministic via hint_offset=index)
        # so each reel scene spotlights a different aspect of the event.
        # The artistic STYLE is unchanged: event-based images use the SAME
        # cel-shaded STYLE_VARIATIONS style as normal mode.
        event_instruction = (
            build_event_image_instruction(event, hint_offset=index)
            if event
            else None
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
    "wide establishing shot",
    "distant cinematic wide shot",
    "long shot",
    "full-scene wide shot",
    "environment-dominant wide composition",
    "distant full-body composition",
]

LENS_STYLES = [
    "24mm wide cinematic lens",
    "24mm environmental lens",
    "28mm wide film lens",
    "28mm cinematic lens",
    "35mm environmental film lens",
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
        # "weather": random.choice(WEATHER_STYLES),
        # "grade": random.choice(COLOR_GRADES),
    }
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
from google.genai import types
from .config import GEMINI_API_KEY, GEMINI_MODEL
from . import PromptSelector as _PS
from .PromptSelector import get_prompt_for_current_time, BASE_INSTRUCTION
from .gender_tracker import get_next_gender, get_gender_instruction
from event_detector import CONTENT_REEL, build_reel_event_instruction, get_today_event
import json
import random

# Timeout in ms. Generating a full story JSON (narration + hook + captions
# + 6 scenes + style) can take 30-90s; 120s is a generous ceiling so a dead
# API fails with a clear message instead of hanging silently forever.
REQUEST_TIMEOUT_MS = 120_000

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
)

MODEL = GEMINI_MODEL

# ---------------------------------------------------------------------------
# HOOK MEMORY — the hook line must feel brand new every reel, never recycled.
# Storage is owned by PromptSelector (reel_hook_tracker.json) so the ban list
# is identical everywhere in the pipeline; these are thin delegates.
# ---------------------------------------------------------------------------


def load_recent_hooks(limit=15):
    """Return the most recent hook lines (newest last) from PromptSelector."""
    try:
        return _PS._load_hook_history()[-limit:]
    except Exception:
        return []


def save_hook_line(hook):
    """Append a generated hook line to PromptSelector's history."""
    try:
        _PS._remember_hook_line(hook)
    except Exception:
        pass


def build_hook_rule():
    """Prompt rule forbidding reuse of recent hooks (uniqueness engine)."""
    hooks = load_recent_hooks()
    base = (
        "- hook_line must be SHORT and punchy: 3-7 words, max 9. It must stop a "
        "scrolling thumb in under a second — a hint, a question, or a flash of "
        "the feeling, never a summary and never a full sentence of the narration"
    )
    if not hooks:
        return base
    recent = "; ".join(f'"{h}"' for h in hooks[-10:])
    return (
        f"{base}\n"
        f"- hook_line must feel BRAND NEW — never reuse or closely imitate the "
        f"wording, structure or opening pattern of these recent hooks: {recent}"
    )

def build_generation_prompt(pinned_key=None) -> str:

    # Get the complete prompt (returns a string, not a dict).
    # pinned_key lets a retry reuse the EXACT same archetype (no re-pick).
    final_prompt = get_prompt_for_current_time(pinned=pinned_key)
    
    # Pick a visual mode from the archetype's preferred pool (diverse, no repeats)
    _arch = getattr(_PS, "LAST_ARCHETYPE_INFO", None) or {}
    visual_mode = get_next_gender(preferred_modes=_arch.get("visual_modes"))
    visual_instruction = get_gender_instruction(visual_mode)

    print(f"\n🎭 Visual mode for this reel: {visual_mode.upper()}")
    
    # Optional enhancement: if today is a configured special event,
    # build the event reel instruction AND an override that makes the event
    # story win over the base "not a story / no events" direction.
    event = get_today_event(content_type=CONTENT_REEL)
    event_instruction = build_reel_event_instruction(event) if event else ""
    event_override = ""
    rule_category = "- narration must strictly follow the selected story type (archetype)"
    rule_event = (
        "- if SPECIAL DATE REEL MODE is present, the narration and scenes must "
        "feel connected to that occasion"
    )

    if event_instruction and event:
        event_name = str(event.get("name", "this occasion")).strip()
        event_override = f"""

==================================================
EVENT DAY OVERRIDE — READ BEFORE WRITING
==================================================
Today is {event_name}. The occasion below overrides EVERYTHING in the base
instruction: today's archetype, theme, hook, ending and mood are all set
aside. Write the 80-110 word nostalgic, first-person memory story
described in SPECIAL DATE REEL MODE. The selected story type only sets
the mood; it NEVER sets the subject. If the story type (e.g. jokes, love
drama, or generic wisdom) contradicts the occasion, choose the occasion's
nostalgic memory instead.
        """
        rule_category = (
            "- TODAY the narration MUST be a nostalgic, first-person memory story "
            "about the occasion listed in SPECIAL DATE REEL MODE; the content "
            "category only supplies mood and is never the subject"
        )
        rule_event = (
            "- TODAY the narration and all 6 scenes must be unmistakably about the "
            "occasion, nostalgic and memory-driven; no generic or unrelated stories"
        )

    # Note: content info is already printed in PromptSelector.get_prompt_for_current_time()

    # Uniqueness rule for the hook line (never repeat recent hooks)
    rule_hooks = build_hook_rule()
    # No need to import or call get_content_type_for_time again

    # Add JSON output format requirements to the prompt
    return f"""
        {final_prompt}

        {event_instruction}
        {event_override}

        ==================================================
        OUTPUT FORMAT

        Return ONLY valid JSON.

        {{
            "content_type": "",
            "title": "",
            "hook_line": "",
            "captions": {{
                "caption_line": "",
                "cta": ""
            }},
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
        - hook_line must be 3-7 words (max 9): the punchiest scroll-stopping teaser for THIS story, written as a caption-style tag, NOT the first line of the narration and NOT the opening spoken sentence (so the video doesn't show the same text twice)
        - the first spoken line of narration must be DIFFERENT from hook_line; the hook is a teaser, the narration opens with the moment
        - captions.caption_line must be the single most shareable line in the narration (may repeat the hook or the final line)
        - captions.cta must be one gentle human question inviting comments or saves (e.g. "Who felt this tonight?"); use "" if no good question comes to mind
        {rule_category}
        {rule_event}
        {rule_hooks}
        - exactly 6 visual scenes
        - each scene must represent one clear visual moment
        - every scene must directly match the narration
        - follow the selected visual mode exactly: {visual_mode}
        - male and female should be treated equally; do not prefer either gender
        - use the same main character throughout all scenes only when the visual mode uses a character
        - if no character is needed, keep the emotional world consistent through place, color, weather, objects, or nature
        - scenes must be illustration-friendly and visually varied
        - avoid repeating the same location unless intentional
        - PERSONS FIRST: at least 4 of the 6 scenes must include ONE ordinary
          person - a boy, a girl, or an older person - doing a simple everyday
          task (crossing a bridge, waiting at a window, walking a street,
          reading, carrying groceries, holding a phone, tying a shoelace,
          watering plants). The scenery is the beautiful background; the person
          in an honest moment is the subject.
        - the remaining 1-2 scenes may be scenery-only (landscape, place, object)
          for breathing room, but never an empty weather shot with no person
        - keep the same person's identity (age and quiet style) across all scenes
          when a character mode is used; vary only the task and the place
        - vary locations strongly: bridge over a river, mountain road, railway
          platform, cafe window, village field, city street, seaside, library,
          rooftop garden, forest path, bus stop - never the same twice
        - avoid sunset as the default AND avoid rain as the default; rotate
          aesthetics: morning mist, golden afternoon, blue hour, moonlight,
          cloudy evening, warm indoor lamps, fog, snow, autumn leaves, lakeside
          breeze, heat haze, streetlights, soft dawn
        - never let the whole reel feel like one weather or one place

        ==================================================
        CHARACTER RULES

        {visual_instruction}

        General rules:
        - PERSONS ARE THE HERO: most scenes (4-5 of 6) feature one ordinary
          person - boy, girl, or older - doing a relatable everyday task. The
          selected visual mode tells you HOW the person appears; follow it.
        - No celebrities, no fantasy characters, no glamour portraits, no selfies
        - Use realistic, simple, relatable clothes when humans appear
        - Prefer medium/wide cinematic shots over close-up faces
        - Keep beautiful scenery everywhere: plants, bridges, rivers, fields,
          mountains, windows, books, cups, letters, lamps, roads, balconies,
          buses, libraries, train stations
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


def annotate_story(data):
    """
    Fill optional fields used by the caption / voice / video steps so the rest
    of the pipeline never depends on a field Gemini forgot.
    """
    info = getattr(_PS, "LAST_ARCHETYPE_INFO", None) or {}
    data.setdefault("archetype", info.get("key"))
    data.setdefault("voice", info.get("voice"))
    data.setdefault("hook_line", "")
    caps = data.get("captions")
    if not isinstance(caps, dict):
        caps = {}
        data["captions"] = caps
    caps.setdefault("caption_line", "")
    caps.setdefault("cta", "")
    return data


def generate_story_json():
    """
    Generate story JSON from Gemini.

    Retry behaviour:
    - Attempt 1 uses the full prompt.
    - If validation fails, one corrective retry with a fresh prompt.
    - If both fail, returns a RANDOM varied fallback story so the fallback is
      never the same canned text twice in a row.
    """
    print("Generating story...")

    max_attempts = 2
    pinned_key = None

    for attempt in range(1, max_attempts + 1):
        try:
            prompt = build_generation_prompt(pinned_key=pinned_key)

            print("⏳ Asking Gemini to write the story... (takes 30-90s, please wait)")

            interaction = client.interactions.create(
                model=MODEL,
                input=prompt
            )

            if interaction.output_text is None:
                raise ValueError("Gemini returned empty response.")

            data = parse_story_json(interaction.output_text)
            annotate_story(data)
            # Remember this hook so the next reel never reuses/imitates it
            save_hook_line(data.get("hook_line"))
            return data

        except Exception as exc:
            print(f"\n⚠️  Generation attempt {attempt}/{max_attempts} failed: {exc}")
            if attempt < max_attempts:
                print("Retrying once with the same archetype...")
                # Pin the same selection so the retry does NOT re-pick an
                # archetype (which would waste the alternation slot).
                pinned_key = getattr(_PS, "LAST_PROMPT_SELECTION", None)

    print("\nUsing a random varied fallback story.")
    return get_demo_story_json()


def get_demo_story_json():
    """
    Fallback: a RANDOM story from a varied bank (never identical back-to-back),
    with all optional fields (visual_style, character, captions) filled in.
    """
    return _build_fallback(random.choice(_FALLBACK_STORIES))


# ===========================================================================
# FALLBACK STORY BANK - varied so a fallback is never identical
# ===========================================================================

_BASE_VISUAL_STYLE = {
    "art_style": "cinematic painterly editorial illustration",
    "palette": "soft muted earth tones with warm lamps and monsoon blues",
    "lighting": "warm window light and soft indoor glow",
    "camera": "medium-wide poetic still frames",
    "aspect_ratio": "9:16",
}

_NO_CHARACTER = {"gender": "none", "age": "N/A", "hair": "N/A", "clothes": "N/A"}


def _build_fallback(data):
    data.setdefault("visual_style", dict(_BASE_VISUAL_STYLE))
    data.setdefault("character", dict(_NO_CHARACTER))
    data.setdefault("hook_line", "")
    data.setdefault("captions", {"caption_line": "", "cta": ""})
    return data


_FALLBACK_STORIES = [
    {
        "content_type": "MICRO_STORY",
        "title": "The Call You Almost Missed",
        "archetype": "MICRO_STORY",
        "voice": "deep_male",
        "hook_line": "The call you almost missed.",
        "captions": {
            "caption_line": "Some calls simply say: I am still here.",
            "cta": ""
        },
        "narration": "That night my father called just to hear my voice. I almost did not answer. I said I was busy, but he only wanted two minutes. He asked about the weather, about food, about nothing at all. Yet his voice carried the whole house with it, the old chair, the running tap, my mother asking who it was. I realized I had not heard him in weeks. Some calls bring no news. They just walk you back to the door of home and make sure you still remember where it is.",
        "visual_mode": "nostalgic_room",
        "scenes": [
            "A phone glowing on a wooden table at night, a finger about to decline the call",
            "A dim kitchen with a running tap and a kettle on the stove",
            "An old armchair by the window holding a folded shawl",
            "A hallway with family photo frames lit by a single lamp",
            "A phone on a bedside table just after being answered",
            "Morning light on the same wooden table, the phone now quiet"
        ]
    },
    {
        "content_type": "REALITY_TALK",
        "title": "Some Doors Close for Your Own Good",
        "archetype": "REALITY_TALK",
        "voice": "calm_male",
        "hook_line": "Some doors close for your own good.",
        "captions": {
            "caption_line": "You are allowed to stop knocking.",
            "cta": ""
        },
        "narration": "You cannot heal in the same place that keeps opening the wound. Letting go sounds cruel, but it is the kindest thing you can give yourself. Some doors only look like home. The people who truly see you do not need a loud announcement. They stay, they show up, they make tea without being asked. Closing a door is not losing. It is finally choosing the rooms where your presence means something. And the one who was meant to stay is already inside.",
        "visual_mode": "abstract_emotion",
        "scenes": [
            "A closed wooden door with warm light leaking from underneath",
            "A road splitting into two paths at evening blue hour",
            "A single key on a windowsill catching the last sun",
            "An open window with a curtain lifting in warm wind",
            "A chair at a small table facing an open room of light",
            "Morning freshness on the same table after the door was left empty"
        ]
    },
    {
        "content_type": "HOPE_AFTER",
        "title": "Light Comes Back Slowly",
        "archetype": "HOPE_AFTER",
        "voice": "warm_female",
        "hook_line": "You made it. Even untidily.",
        "captions": {
            "caption_line": "Rebuilding is still building.",
            "cta": ""
        },
        "narration": "Healing is not a clean line, but it is still moving forward. Some days you woke up tired and cried and still went out and existed. That counts. Nobody was watching while you rebuilt, but you did. The plants grew on your window because of the little sun you let in. Look at yourself now, softer around the edges, stronger underneath. You are not where you started. You made it here, somehow. Your kind heart is still beating. Light comes back slowly. It always comes back.",
        "visual_mode": "nature",
        "scenes": [
            "First warm light breaking over a quiet field after rain",
            "A small green shoot growing between wet tile cracks",
            "A window ledge with two plants turning toward morning",
            "A hand holding a cup of tea with steam rising in soft light",
            "A garden path drying after monsoon rain",
            "Soft dawn over the same field, warm and calm"
        ]
    },
    {
        "content_type": "DESI_SLICE",
        "title": "Rain at the Chai Stall",
        "archetype": "DESI_SLICE",
        "voice": "soft_female",
        "hook_line": "First rain at the chai stall.",
        "captions": {
            "caption_line": "Some happiness lives at the tea stall in the rain.",
            "cta": ""
        },
        "narration": "The first rain came like a small festival. We rushed under the tin roof of the chai stall, strangers sharing the same seconds of weather. The kettle went faster, the steam mixed with wet earth, someone sang a film line and everyone half smiled. For one while, nobody was alone. We drank from small glasses, the rain drumming above us like an old friend. Then it slowed, the glasses returned, and every person went their separate way. But to this day, that one inch of rain was the closest we all ever felt to home.",
        "visual_mode": "rainy_city",
        "scenes": [
            "One tin-roof chai stall by a street soaked in monsoon rain",
            "Steam rising from a brass kettle in soft grey light",
            "A few people with small tea glasses under the tin roof",
            "Rain splashing into dark puddles reflecting the stall bulb",
            "Empty glasses collected as the rain turns to drizzle",
            "Puddle mirror of the quiet street after the rain stops"
        ]
    },
    {
        "content_type": "LETTER_FORMAT",
        "title": "A Letter to Me Before It Got Hard",
        "archetype": "LETTER_FORMAT",
        "voice": "soft_female",
        "hook_line": "Dear the me I used to be...",
        "captions": {
            "caption_line": "You did not ruin anything. You were learning.",
            "cta": ""
        },
        "narration": "Dear the version of me from five years ago, you think everything is falling. It is not. You will lose a few people, cry in quiet rooms, doubt every choice, then wash your face and keep moving. You will make mistakes and laugh about them later. You were never weak. You were a whole human disappearing stories, still learning how to stand. I want you to know you became okay, on your own terms, with your heart still open. Do not be scared. Look how far we are. Keep going.",
        "visual_mode": "object",
        "scenes": [
            "An old diary open on a desk with a pen resting on the pages",
            "A lamp over a study desk with scuffed edges",
            "A window with a paper plane on the sill",
            "A worn backpack against a bedroom chair",
            "A gentle hand closing the diary",
            "Soft window light warming the closed diary"
        ]
    },
    {
        "content_type": "JOY_QUIET",
        "title": "The Quiet Joy of Belonging",
        "archetype": "JOY_QUIET",
        "voice": "warm_female",
        "hook_line": "Happiness is a small ordinary thing.",
        "captions": {
            "caption_line": "Keep every quiet happy thing. It is enough.",
            "cta": ""
        },
        "narration": "Some happiness is so quiet we forget to name it. First rain on dry earth. Home food after a long journey. A saved message you re-read on a hard day. A Sunday with no plans. The kind of laughter that leaves your stomach soft. The sudden health of the people you love. It all counts. The world sells happiness as loud, but one soft evening where nothing is wrong is already everything. Own it. Let the small gladness be enough.",
        "visual_mode": "animal_life",
        "scenes": [
            "A stray cat napping by a warm shop wall in early morning",
            "A window with steam rising from two cups of tea",
            "A kitchen bench with fresh chapati and tomatoes",
            "A pair of birds on a wire in golden light",
            "A dog resting at a sunny street corner",
            "Warm evening light over a quiet rooftop with plants"
        ]
    }
]



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

    if words < 80 or words > 110:
        raise ValueError(
            f"Narration must be between 80-110 words. Current: {words}"
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

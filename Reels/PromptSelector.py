"""Creative selection and prompt building for Aesthetic Vibes reels."""

import json
import os
import random
import re
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Local no-repeat memory (like gender_tracker uses)
# ---------------------------------------------------------------------------

HOOK_CACHE_FILE = Path.home() / ".cache" / "reel_hook_tracker.json"
HOOK_HISTORY_LIMIT = 30
CACHE_FILE = Path.home() / ".cache" / "reel_prompt_tracker.json"


def _load_cache() -> dict:
    default = {
        "archetypes": [], "themes": [], "formats": [], "recent_dna": [],
    }
    try:
        if CACHE_FILE.exists():
            cached = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(cached, dict):
                default.update(cached)
                return default
    except (OSError, ValueError):
        pass
    return default


def _save_cache(cache: dict) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
    except OSError:
        pass


def _load_hook_history() -> list:
    try:
        if HOOK_CACHE_FILE.exists():
            cached = json.loads(HOOK_CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(cached, list):
                hooks = [
                    " ".join(str(item).split()).lower()
                    for item in cached
                    if " ".join(str(item).split())
                ]
                return hooks[-HOOK_HISTORY_LIMIT:]
    except (OSError, ValueError):
        pass
    return []


def _prune_recent_hook_lines(hook_lines: list, hook_history: list) -> list:
    """
    Keep only hook lines that are meaningfully different from recent reels.
    A line is rejected when it duplicates a recent hook, starts/ends like one,
    or shares most of its substance with one.
    """
    fresh_lines = []

    for hook in hook_lines:
        candidate = " ".join(str(hook).split()).lower()
        if not candidate:
            continue

        dominated = False
        candidate_words = set(re.findall(r"[a-z']+", candidate))
        for old in hook_history[-HOOK_HISTORY_LIMIT:]:
            old_words = set(re.findall(r"[a-z']+", old))
            if (
                candidate == old
                or candidate.startswith(old[:25])
                or old.startswith(candidate[:25])
            ):
                dominated = True
                break
            if candidate_words and old_words:
                shared = candidate_words & old_words
                shorter = min(len(candidate_words), len(old_words))
                if shorter >= 3 and len(shared) / shorter >= 0.7:
                    dominated = True
                    break

        if not dominated:
            fresh_lines.append(" ".join(str(hook).split()))

    return fresh_lines


def _save_hook_history(hook_history: list) -> None:
    try:
        HOOK_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        HOOK_CACHE_FILE.write_text(
            json.dumps(hook_history[-HOOK_HISTORY_LIMIT:], ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass


def _format_recent_hooks(hook_history: list, pinned_block=None) -> str:
    """
    Human-readable block of recent hook lines shown to Gemini as the
    do-not-repeat list.

    pinned_block: when a retry reuses a pinned selection, pass the block
    text stored in LAST_PROMPT_SELECTION so the retry prompt is byte-for-
    byte identical (no new formatting drift).
    """
    if pinned_block:
        return str(pinned_block)

    recent = [
        " ".join(str(h).split())
        for h in (hook_history or [])
        if str(h).strip()
    ][-12:]

    if not recent:
        return (
            "(no recent hooks recorded - this is the first reel, so write "
            "anything fresh)"
        )

    numbered = "\n".join(f"- {h}" for h in recent)
    return (
        "RECENT HOOKS (never reuse, paraphrase, or echo any of these):\n"
        f"{numbered}"
    )


def _remember_hook_line(hook_line: str) -> None:
    hook = " ".join(str(hook_line or "").split())
    if not hook:
        return
    hook_history = _load_hook_history()
    hook_history.append(hook.lower())
    _save_hook_history(hook_history)


def remember_generated_story(story_payload=None, hook_line: str = ""):
    """Persist a generated hook so future hooks remain different."""
    story = _parse_story_payload(story_payload)
    hook = " ".join(str(story.get("hook_line") or hook_line or "").split())
    if hook:
        _remember_hook_line(hook)


def _hooks_have_substance(lines: list) -> bool:
    """Ensure hook beats are not generic fragments such as 'breath'."""
    for line in lines:
        words = [word for word in re.findall(r"[a-zA-Z']+", line) if len(word) > 2]
        if len(words) < 3:
            return False
    return True


def _split_hook_lines(hook_line: str) -> list:
    raw = (hook_line or "").replace("\\n", "\n")
    lines = [part.strip() for part in raw.splitlines() if part.strip()]
    cleaned = [re.sub(r"^\W+|\W+$", "", part) for part in lines]
    return [part for part in cleaned if part]


def _parse_story_payload(raw_story) -> dict:
    if isinstance(raw_story, dict):
        return raw_story
    try:
        return json.loads(str(raw_story or ""))
    except (ValueError, TypeError):
        return {}


def _pick_no_repeat(pool, history_key, cache, history_len=2):
    """Pick a random item from pool avoiding items toto recent history."""
    history = cache.get(history_key, [])
    recent = set(history[-history_len:])
    candidates = [item for item in pool if item not in recent]
    if not candidates:
        candidates = list(pool)
    return random.choice(candidates)


# ===========================================================================
# CORE WRITING INSTRUCTION
# ===========================================================================

BASE_INSTRUCTION = """You write short, heartfelt voiceovers for Reels on "Aesthetic Vibes" - a page for lost souls finding their way home through words.

Readership: 90% South Asian (India, Bangladesh, Nepal, Pakistan), 18-35, mostly women. The words should feel personal, relatable, touching, and worth saving or sharing.

LANGUAGE:
- Simple English, like telling a friend over chai or refusing between.
- No long, fancy, heavy or rare words. The feeling must land in one listen.
- Short sentences with natural breathing pauses (line breaks = pauses).
- Calm, mature tone. Never a motivational speaker. No cliches.

CREATIVE FREEDOM:
- Follow the selected purpose, viewer intent, pillar, format, and arc as a coherent direction.
- The arc is optional guidance, not a checklist. Do not force a twist, reversal, concrete object, punch line, or dramatic final line.
- Use a concrete or desi detail only when it belongs naturally to the idea. Never insert chai, rain, a phone, or any object just to satisfy a rule.
- A reel may be quiet, funny, warm, direct, unfinished, or deeply emotional.

SAFETY - always:
- No names that are not obviously ordinary, no celebrities.
- No politics, religion debates, hate, or violence.
- Keep it original. Never copy songs, poems, speeches or famous quotes.
- Be gentle. Hard truths are okay; cruelty is not.
"""


# ===========================================================================
# CREATIVE ARCHITECTURE
# ===========================================================================
# The selected values are injected into the prompt one at a time. They are
# preferences for a creative direction, not a checklist every reel must pass.
# ===========================================================================

CREATIVE_ARCS = {
    "EMOTIONAL_REALIZATION": "tension -> recognition -> realization, when the idea genuinely needs movement",
    "MICRO_STORY": "scene -> detail -> meaning; let the moment reveal the point",
    "ADVICE": "problem -> truth -> useful practical thought, without lecturing",
    "CONFIDENCE": "doubt -> realization -> quiet confidence",
    "NOSTALGIA": "memory -> specific detail -> what it means now",
    "POEM": "feeling -> images -> emotional release, with no forced twist",
    "FUNNY": "situation -> escalation -> punchline or deadpan observation",
    "WARM": "ordinary moment -> appreciation -> a small smile",
    "BOLD_TRUTH": "assumption -> contradiction -> clear truth",
    "OBSERVATIONAL": "observation -> example -> unexpected insight",
    "LETTER": "address -> memory or thought -> intimate closing",
    "ROMANTIC": "moment -> detail -> feeling, without melodrama",
    "NO_ARC": "one honest thought that can end naturally; no required turn",
}

VIEWER_INTENTS = {
    "IDENTIFICATION": "make the viewer think: this is literally me",
    "SEND_TO_SOMEONE": "make the viewer think of one person to send it to",
    "YOU_NEED_THIS": "offer something someone quietly needs to hear",
    "NOSTALGIA": "bring back home, childhood, or a time that felt ordinary then",
    "FRIENDSHIP": "make the viewer think: this is us",
    "FAMILY": "bring to mind a parent, sibling, or home",
    "LAUGHTER": "make the viewer laugh because it is painfully accurate",
    "SAVE": "make the viewer want to remember the thought",
    "COMMENT": "leave room for a genuine personal response",
    "HOPE": "leave the viewer lighter without forced positivity",
    "CONFIDENCE": "make the viewer want to become this version of themselves",
    "WARMTH": "make the viewer smile at an ordinary good moment",
    "REFLECTION": "make the viewer see a familiar thing differently",
}

CONTENT_PURPOSES = {
    "RECOGNIZE": "name a familiar human experience precisely",
    "REMEMBER": "bring a person, place, or time back to mind",
    "COMFORT": "offer companionship without trying to fix everything",
    "AMUSE": "turn an everyday contradiction into a laugh",
    "NOTICE": "show an overlooked detail or social truth",
    "ENCOURAGE": "give grounded courage without generic motivation",
    "CONNECT": "create something people send to someone they love",
    "RETHINK": "change how the viewer sees a familiar choice",
}

FORMAT_RANGES = {
    "prose": (80, 110), "poem": (55, 90), "micro_story": (80, 110),
    "short_reflection": (50, 80), "advice": (60, 100), "funny": (35, 70),
    "letter": (80, 110), "observational": (45, 80),
}

HOOK_BEHAVIORS = {
    "CURIOSITY": "open with an unfinished thought that creates curiosity",
    "CONFESSION": "open with a plain personal confession",
    "SCENE": "open inside a specific scene, place, or time",
    "QUESTION": "open with a natural question",
    "CONTRADICTION": "open with a statement that seems to disagree with itself",
    "DIALOGUE": "open with a short line of believable dialogue",
    "FUNNY": "open with a dry, recognizable joke or observation",
    "NOSTALGIA": "open with a memory whose meaning is not yet clear",
    "DIRECT": "open by saying the truth plainly",
    "ACTION": "open with a small action already happening",
    "POETIC": "open with one simple image, only when it feels natural",
    "OBSERVATIONAL": "open with something people rarely say out loud",
}

ENDING_BEHAVIORS = {
    "PUNCHLINE": "end with a funny turn or dry punchline",
    "REALIZATION": "let the meaning become clear at the end",
    "OPEN_ENDING": "leave the thought open without explaining it",
    "WARM_ENDING": "land gently on appreciation or connection",
    "QUESTION": "end with a genuine question, not a slogan",
    "FULL_CIRCLE": "make the opening mean something new",
    "QUIET_FACT": "end on a simple fact without announcing its meaning",
    "DIRECT_ADVICE": "end with one useful, human suggestion",
    "DIALOGUE_ECHO": "return to a line of believable speech",
    "NOSTALGIC_END": "end with what the remembered time means now",
    "EMOTIONAL_RELEASE": "allow the feeling to loosen without overexplaining",
    "NO_BIG_ENDING": "stop naturally; do not manufacture a climax",
    "UNDERSTATED_ENDING": "end plainly and let the viewer do the feeling",
}

PACING_STYLES = {
    "SLOW": "slow, spacious sentences with room to breathe",
    "CONVERSATIONAL": "natural speech with varied sentence lengths",
    "QUICK": "short beats and quick movement",
    "RHYTHMIC": "intentional line breaks and a light musical cadence",
    "STORYTELLING": "clear scene progression and lived details",
    "DEADPAN": "flat, dry delivery that makes the contrast funny",
    "POETIC": "simple images and measured pauses without fancy language",
    "DIRECT": "plain statements with little decoration",
}

CREATIVE_TEMPERATURES = {
    "LOW": "quiet, observational, or warm; no need to peak emotionally",
    "MEDIUM": "engaging and emotionally clear but natural",
    "HIGH": "strong emotional or comedic impact, without melodrama",
}

EVERYDAY_DETAILS = [
    "a phone, missed call, or voice note", "an old photograph or school notebook",
    "a lunchbox, grocery receipt, or train ticket", "a parent's handwriting or sandals",
    "a half-written message, keychain, or old T-shirt", "a lift button, hostel cupboard, or office badge",
    "an alarm at 6:30, college ID, or restaurant bill", "a kitchen light, empty chair, or balcony",
    "a metro card, bus window, or shopping bag", "a childhood toy, folded clothes, or medicine strip",
]

HOOK_OPTIONS_BY_KEY = {
    "MICRO_STORY": ["SCENE", "CURIOSITY", "DIALOGUE", "ACTION"],
    "WISDOM_TRUTH": ["OBSERVATIONAL", "CONTRADICTION", "DIRECT", "CURIOSITY"],
    "REALITY_TALK": ["DIRECT", "CONTRADICTION", "QUESTION", "OBSERVATIONAL"],
    "HOPE_AFTER": ["CONFESSION", "CURIOSITY", "DIRECT", "POETIC"],
    "LETTER_FORMAT": ["DIRECT", "CONFESSION", "DIALOGUE", "NOSTALGIA"],
    "DESI_SLICE": ["SCENE", "NOSTALGIA", "DIALOGUE", "ACTION"],
    "JOY_QUIET": ["SCENE", "CONFESSION", "OBSERVATIONAL", "FUNNY"],
    "RELATABLE_POEM": ["CONFESSION", "QUESTION", "POETIC", "OBSERVATIONAL"],
    "HEALING_POEM": ["CONFESSION", "POETIC", "CURIOSITY", "QUESTION"],
}

ENDING_OPTIONS_BY_KEY = {
    "MICRO_STORY": ["REALIZATION", "DIALOGUE_ECHO", "QUIET_FACT", "FULL_CIRCLE"],
    "WISDOM_TRUTH": ["OPEN_ENDING", "QUIET_FACT", "REALIZATION", "UNDERSTATED_ENDING"],
    "REALITY_TALK": ["DIRECT_ADVICE", "QUIET_FACT", "OPEN_ENDING", "UNDERSTATED_ENDING"],
    "HOPE_AFTER": ["WARM_ENDING", "EMOTIONAL_RELEASE", "REALIZATION", "UNDERSTATED_ENDING"],
    "LETTER_FORMAT": ["DIALOGUE_ECHO", "WARM_ENDING", "NOSTALGIC_END", "OPEN_ENDING"],
    "DESI_SLICE": ["WARM_ENDING", "NOSTALGIC_END", "QUIET_FACT", "NO_BIG_ENDING"],
    "JOY_QUIET": ["WARM_ENDING", "PUNCHLINE", "NO_BIG_ENDING", "UNDERSTATED_ENDING"],
    "RELATABLE_POEM": ["EMOTIONAL_RELEASE", "OPEN_ENDING", "UNDERSTATED_ENDING", "WARM_ENDING"],
    "HEALING_POEM": ["EMOTIONAL_RELEASE", "WARM_ENDING", "OPEN_ENDING", "UNDERSTATED_ENDING"],
}

PILLAR_OPTIONS_BY_KEY = {
    "MICRO_STORY": ["FAMILY", "FRIENDSHIP", "RELATIONSHIPS", "ADULTING"],
    "WISDOM_TRUTH": ["LIFE_CHOICES", "OBSERVATIONAL", "BOLD_TRUTH", "PERSONAL_GROWTH"],
    "REALITY_TALK": ["SELF_RESPECT", "CONFIDENCE", "BOLD_TRUTH", "LIFE_CHOICES"],
    "HOPE_AFTER": ["HOPE", "HEALING", "PERSONAL_GROWTH", "SMALL_HAPPINESS"],
    "LETTER_FORMAT": ["FAMILY", "FRIENDSHIP", "ROMANCE", "RELATIONSHIPS"],
    "DESI_SLICE": ["DESI_DAILY_LIFE", "COLLEGE_YOUTH", "CHILDHOOD", "FAMILY"],
    "JOY_QUIET": ["SMALL_HAPPINESS", "FUNNY_REAL_LIFE", "FRIENDSHIP", "DESI_DAILY_LIFE"],
    "RELATABLE_POEM": ["RELATIONSHIPS", "ADULTING", "HEALING", "IDENTITY"],
    "HEALING_POEM": ["HEALING", "HOPE", "PERSONAL_GROWTH", "SELF_RESPECT"],
}

BANNED_PLATITUDES = [
    "you are enough",
    "you're enough",
    "stay strong",
    "you've got this",
    "you got this",
    "everything happens for a reason",
    "trust the process",
    "this too shall pass",
    "never give up",
    "keep going",
    "believe in yourself",
    "just be yourself",
    "love yourself first",
    "be kind to yourself",
    "happiness is a choice",
    "the best is yet to come",
    "good things take time",
    "time heals",
    "one day at a time",
    "it is what it is",
    "everything will be okay",
    "everything will be fine",
    "life goes on",
    "hard work pays off",
    "you deserve the world",
    "follow your heart",
    "dream big",
    "let it go",
    "you matter",
    "and that's okay",
    "and it's okay",
]

# Concrete anchors that make a narration feel lived instead of invented.
# Matched on word boundaries so "tea" never fires inside "teach".
CONCRETE_SIGNAL_WORDS = [
    "chai", "tea", "kettle", "cup", "glass", "thermos", "tiffin", "plate",
    "spoon", "cooker", "rice", "roti", "chapati", "pickle", "mango", "market",
    "stall", "shop", "shopkeeper", "rickshaw", "auto", "scooter", "bicycle",
    "cycle", "helmet", "ticket", "bus", "train", "platform", "metro", "berth",
    "phone", "charger", "screen", "battery", "call", "letter", "envelope",
    "diary", "notebook", "pen", "page", "book", "lamp", "bulb", "switch",
    "fan", "radio", "song", "saree", "kurta", "dupatta", "sweater", "shoe",
    "sandal", "locket", "ring", "thread", "bangle", "photo", "album", "frame",
    "window", "balcony", "roof", "terrace", "gate", "stairs", "staircase",
    "corridor", "wall", "door", "lock", "key", "mirror", "jar", "blanket",
    "pillow", "bed", "table", "chair", "bench", "basket", "bag", "plant",
    "flower", "leaf", "dog", "cat", "crow", "pigeon", "kite", "umbrella",
    "puddle", "dust", "streetlight", "pole", "school", "college", "office",
    "library", "hospital", "saloon", "candle", "curtain", "apron", "bucket",
    "tap", "pressure", "incense",
]

_CONCRETE_RE = re.compile(
    r"\b(" + "|".join(sorted(set(CONCRETE_SIGNAL_WORDS))) + r")\b",
    re.IGNORECASE,
)


def find_platitudes(text: str) -> list:
    """
    Return the banned platitude phrases present in ``text`` (lowercase, in
    declaration order). Used by the prompt (as a ban list) and by
    story_generation's validator (as a hard gate on flat drafts).
    """
    normalized = " ".join(str(text or "").lower().split())
    if not normalized:
        return []
    return [phrase for phrase in BANNED_PLATITUDES if phrase in normalized]


def has_concrete_signal(text: str) -> bool:
    """
    True when the narration carries a concrete anchor: an exact number/time,
    one line of real speech in double quotes, or a named ordinary object
    (chai glass, tiffin, ticket, balcony, ...).

    This is the difference between a reel that makes a stranger feel seen and
    a reel that reads like a mood board.
    """
    raw = str(text or "")
    if not raw.strip():
        return False
    if re.search(r"\d", raw):
        return True
    # Only double quotes count as speech, so an apostrophe in "don't" can
    # never be mistaken for a quoted line.
    if re.search(r'["\u201c][^"\u201c\u201d]{3,80}["\u201d]', raw):
        return True
    return _CONCRETE_RE.search(raw) is not None

_BANNED_FOR_PROMPT = ", ".join(f'"{p}"' for p in BANNED_PLATITUDES)

# ===========================================================================
# WEEKDAY ENERGY ENVELOPE (merged with time-of-day mood, never replacing it)
# ===========================================================================

WEEKDAY_DIRECTION = {
    0: ("Monday - steady push", "grounded, move steady, small steps"),
    1: ("Tuesday - quiet comfort", "gentle warmth, soft comfort"),
    2: ("Wednesday - mid-week honesty", "a soft realization or an honest check-in"),
    3: ("Thursday - real talk", "respectful, direct, clear-eyed"),
    4: ("Friday - lightness", "something light, joyful or relieving"),
    5: ("Saturday - slow", "rest, friends, simple pleasures"),
    6: ("Sunday - memory", "family, childhood, reflection, nostalgia"),
}


def get_weekday_direction():
    """Return (label, direction) for today."""
    return WEEKDAY_DIRECTION.get(datetime.now().weekday(), ("", ""))


# ===========================================================================
# REEL ARCHETYPES - the diversity engine
# ===========================================================================

KICK_ENGINE = f"""
==================================================
SELECTED CREATIVE DIRECTION
==================================================
Use the selected creative arc naturally. Do not manufacture a twist because a
twist is expected. A powerful reel may simply observe, remember, amuse, advise,
or end quietly. Let the selected format, pacing, temperature, and ending decide
how much movement the piece needs.

Concrete details are optional. Use one only when it makes the idea more real;
never add a random object merely to satisfy a prompt. Vary sentence lengths
when the selected pacing calls for it, but do not force a short punch line.

BANNED PLATITUDES - use this as a safety net, not as the creative engine:
{_BANNED_FOR_PROMPT}
"""

ARCHETYPES = [
    {
        "format": "prose", "key": "MICRO_STORY", "name": "Micro Story",
        "script": "ONE specific everyday moment told like a memory. Tell it scene by scene; let the story make the truth.",
        "hook_styles": ["Start with the moment itself", "Start with one small gesture", "Start with a place and time", "Start with a journal-style line"],
        "ending_styles": ["End with the quiet truth", "End with what you would tell them now", "End warm and human"],
        "themes": ["a parent's repeated phone call you almost ignored", "a goodbye said casually that stayed forever", "the last bus home after everything changed", "a friend's voice after years of silence", "a small habit that quietly saved a hard month"],
        "visual_modes": ["bridge", "nostalgic_room", "female", "male", "landscape", "friends_or_couple"], "voice": "deep_male",
    },
    {
        "format": "prose", "key": "WISDOM_TRUTH", "name": "Wisdom Truth",
        "script": "A calm, universal truth learned from living. No story characters; let one central idea unfold naturally.",
        "hook_styles": ["Start with a quiet realization", "Start with a journal thought", "Start with something experience teaches", "Start with a contradiction"],
        "ending_styles": ["End with a universal life lesson", "End with acceptance", "End with a peaceful realization"],
        "themes": ["people change and love changes shape", "growing up means saying goodbye quietly", "outgrowing versions of ourselves", "the small habits that built you", "the roads you did not take"],
        "visual_modes": ["landscape", "bridge", "object", "abstract_emotion", "nostalgic_room", "architecture"], "voice": "calm_male",
    },
    {
        "format": "prose", "key": "REALITY_TALK", "name": "Real Talk",
        "script": "One caring reality check: direct, warm, and never cruel. It should feel like a wise friend, not a lecture.",
        "hook_styles": ["Start with the honest sentence", "Start with a wake-up observation", "Start with a hard truth gently", "Start with nobody warns you about this"],
        "ending_styles": ["End with self-respect", "End with a kind boundary", "End with the choice that is yours"],
        "themes": ["you cannot heal in the place that keeps breaking you", "protecting your energy is not selfish", "some doors close", "being everyone's listener has a cost", "wanting peace is not giving up"],
        "visual_modes": ["abstract_emotion", "bridge", "architecture", "landscape", "female", "male"], "voice": "calm_male",
    },
    {
        "format": "prose", "key": "HOPE_AFTER", "name": "Hope After Everything",
        "script": "A warm voiceover showing that the hard part does not have the last word. Keep hope grounded and never forced.",
        "hook_styles": ["Start with a quiet promise", "Start with what kept you going", "Start with a first good morning", "Start with a small sign"],
        "ending_styles": ["End with a hopeful truth", "End with gratitude", "End with a warm forward step"],
        "themes": ["healing is not linear but real", "light returns slowly", "rebuilding with no one watching", "letting go made room", "peace growing around pain"],
        "visual_modes": ["landscape", "bridge", "female", "friends_or_couple", "nature", "object"], "voice": "warm_female",
    },
    {
        "format": "prose", "key": "LETTER_FORMAT", "name": "A Letter",
        "script": "Write a short intimate letter addressed to a younger self, friend, parent, or past love. Keep it universal.",
        "hook_styles": ["Start with the address line", "Start with what you would change", "Start with to the version of me", "Start with what they should know"],
        "ending_styles": ["End with what to remember", "End with a warm signature", "End with advice as forgiveness"],
        "themes": ["a letter to your younger self", "a letter to a friend who left town", "a letter to a parent", "a letter before healing", "a letter to a love that taught you to leave"],
        "visual_modes": ["nostalgic_room", "landscape", "bridge", "female", "male", "object"], "voice": "soft_female",
    },
    {
        "format": "prose", "key": "DESI_SLICE", "name": "Desi Slice of Life",
        "script": "A specific South Asian everyday scene. The beauty is in ordinary reality, not a forced lesson or object.",
        "hook_styles": ["Start with the desi moment", "Start with a smell or sound", "Start with a hostel or college memory", "Start with a bus seat or street"],
        "ending_styles": ["End with the warmth it carried", "End with what we forget to thank", "End with the world feeling"],
        "themes": ["a tea stall in the rain", "a metro ride that became home", "a phone call from home", "hostel food and the nights it held", "a festival window seat"],
        "visual_modes": ["bridge", "rainy_city", "landscape", "nostalgic_room", "friends_or_couple", "animal_life"], "voice": "soft_female",
    },
    {
        "format": "prose", "key": "JOY_QUIET", "name": "Quiet Joy",
        "script": "Capture ordinary happiness: light, gentle, specific, and allowed to simply make someone smile.",
        "hook_styles": ["Start with the small joy", "Start with what today felt like", "Start with catching yourself smiling", "Start with something ordinary you protect"],
        "ending_styles": ["End with the worth of small gladness", "End with permission to enjoy it", "End with a simple exhale"],
        "themes": ["first rain after heat", "a home-cooked meal", "a song saving a day", "a Sunday with no plans", "small wins"],
        "visual_modes": ["landscape", "bridge", "nature", "friends_or_couple", "animal_life", "object"], "voice": "warm_female",
    },
    {
        "format": "poem", "key": "RELATABLE_POEM", "name": "Poem (Relatable)",
        "script": "Write a simple free-verse poem about an everyday feeling. Use a steady cadence without forcing metaphors or a dramatic ending.",
        "hook_styles": ["Begin with the everyday moment", "Begin with a whispered question", "Begin with an ordinary thing", "Begin with a plain confession"],
        "ending_styles": ["End with soft acceptance", "Turn the ache into kindness", "End with a sendable line"],
        "themes": ["saying I'm fine", "overthinking at 1am", "seeking a parent's approval", "the friend who always gives", "a rented room far from home", "growing up away from home", "a love already ending", "talking to yourself"],
        "visual_modes": ["nostalgic_room", "bridge", "landscape", "female", "abstract_emotion", "friends_or_couple"], "voice": "soft_female",
    },
    {
        "format": "poem", "key": "HEALING_POEM", "name": "Poem (Healing)",
        "script": "Write a plain, gentle healing poem. Start wherever the feeling naturally starts and let it end without forcing a climax.",
        "hook_styles": ["Begin with the ache", "Begin with the night", "Begin with what broke", "Begin with light returning"],
        "ending_styles": ["End with lighter days", "End with permission", "End with a warm image"],
        "themes": ["light after a dark season", "being gentle with yourself", "asking for help", "rebuilding in ordinary ways", "grief becoming softer", "forgiving yourself", "not checking old messages"],
        "visual_modes": ["landscape", "bridge", "nature", "abstract_emotion", "friends_or_couple", "object"], "voice": "warm_female",
    },
]

"""
            "End with a universal life lesson",
            "End with acceptance",
            "End with a peaceful realization",
        ],
        "themes": [
            "people change and love changes shape",
            "growing up means saying goodbye quietly",
            "we outgrow versions of ourselves we used to know",
            "the small habits that actually built you",
            "the roads you did not take also shaped you",
        ],
        "visual_modes": ["landscape", "bridge", "object", "abstract_emotion", "nostalgic_room", "architecture"],
        "voice": "calm_male",
    },
    {
        "format": "prose",
        "key": "REALITY_TALK",
        "name": "Real Talk",
        "script": "One caring reality check - the truth you wish someone had told you earlier. Direct, warm, never cruel. It should feel like a wise friend, not a lecture.",
        "hook_styles": [
            "Start with the honest sentence no one says aloud",
            "Start with a wake-up observation",
            "Start with a hard truth delivered gently",
            "Start with 'Nobody warns you about this part'",
        ],
        "ending_styles": [
            "End with self-respect",
            "End with a clear, kind boundary",
            "End with the choice that is still yours",
        ],
        "themes": [
            "you cannot heal in the place that keeps breaking you",
            "protecting your energy is not selfish",
            "some doors close and it is your job to not keep knocking",
            "being everyone's listener has a cost only you notice",
            "wanting peace is not the same as giving up",
        ],
        "visual_modes": ["abstract_emotion", "bridge", "architecture", "landscape", "female", "male"],
        "voice": "calm_male",
    },
    {
        "format": "prose",
        "key": "HOPE_AFTER",
        "name": "Hope After Everything",
        "script": "The positive mirror. A warm, healing voice over - proof that the hard part does not have the last word. Sunrise, growth, light, gentle triumph.",
        "hook_styles": [
            "Start with a quiet promise of better days",
            "Start with what kept you going when nothing made sense",
            "Start with the first good morning after a long night",
            "Start with a small sign that it was, actually, going to be okay",
        ],
        "ending_styles": [
            "End with a hopeful truth",
            "End with gratitude",
            "End with a warm forward step",
        ],
        "themes": [
            "healing is not linear but it is real",
            "the light returns slowly and that is okay",
            "you rebuilt yourself with no one watching - and it worked",
            "letting go made room for the right thing",
            "peace is not absence of pain but growth around it",
        ],
        "visual_modes": ["landscape", "bridge", "female", "friends_or_couple", "nature", "object"],
        "voice": "warm_female",
    },
    {
        "format": "prose",
        "key": "LETTER_FORMAT",
        "name": "A Letter",
        "script": "Write it as a short letter: Dear 18-year-old-me, or Dear friend who stayed, or Dear the one I used to be. Intimate, personal, addressed - but still universal enough that anyone feels it is for them.",
        "hook_styles": [
            "Start with the address line - Dear...",
            "Start with what you would change if the letter could reach them",
            "Start with 'to the version of me from...'",
            "Start with the thing you wish they knew back then",
        ],
        "ending_styles": [
            "End with what you want them to always remember",
            "End with a signature-style line (warm)",
            "End with advice as forgiveness",
        ],
        "themes": [
            "a letter to the younger self before it got hard",
            "a letter to the friend who left town",
            "a letter to the parent who tried their best",
            "a letter to yourself before you healed",
            "a letter to the love that taught you how to leave",
        ],
        "visual_modes": ["nostalgic_room", "landscape", "bridge", "female", "male", "object"],
        "voice": "soft_female",
    },
    {
        "format": "prose",
        "key": "DESI_SLICE",
        "name": "Desi Slice of Life",
        "script": "A small, specific South Asian everyday scene: monsoon rain on the window, chai at home, a metro ride, a hostel night, a phone call from mom, an exam morning. The beauty is the ordinary reality of it.",
        "hook_styles": [
            "Start with the specific desi moment (rain, chai, metro, mama phone call)",
            "Start with the smell or sound that means home",
            "Start with a hostel or college memory",
            "Start with a bus seat, a window, a street",
        ],
        "ending_styles": [
            "End with the warmth the ordinary moment carried",
            "End with what we forget to thank because it is everyday",
            "End with that world feeling",
        ],
        "themes": [
            "monsoon at a tea stall", 
            "the metro ride that one day became home",
            "the phone call from home you almost missed",
            "hostel food and the nights it held",
            "the Diwali smell of oil lamps anda window seat",
        ],
        "visual_modes": ["bridge", "rainy_city", "landscape", "nostalgic_room", "friends_or_couple", "animal_life"],
        "voice": "soft_female",
    },
    {
        "format": "prose",
        "key": "JOY_QUIET",
        "name": "Quiet Joy",
        "script": "Ordinary happiness that deserves a video: first rain on parched earth, home-cooked food after a long week, a saved message that still helps, a Sunday that was actually restful. Light, gentle, shareable.",
        "hook_styles": [
            "Start with the exact small joy itself",
            "Start with what today finally felt like",
            "Start with the moment you caught yourself smiling",
            "Start with something ordinary you now protect",
        ],
        "ending_styles": [
            "End with the worth of small gladness",
            "End with permission to enjoy the quiet",
            "End with a simple exhale",
        ],
        "themes": [
            "the first rain after months of heat",
            "a homecooked meal after a long week",
            "a song that saved a whole day",
            "a Sunday with no plans at all",
            "small wins that happiness is made of",
        ],
        "visual_modes": ["landscape", "bridge", "nature", "friends_or_couple", "animal_life", "object"],
        "voice": "warm_female",
    },
    {
        "format": "poem",
        "key": "RELATABLE_POEM",
        "name": "Poem (Relatable)",
        "script": ("A short RHYTHMIC free-verse poem in the SIMPLEST everyday words about a feeling almost everyone has lived: "
                    "the one who says 'I'm fine', overthinking at 1am, the daughter still seeking a parent's approval, "
                    "the person in a rented room far from home, the friend who always gives. No big metaphors, no heavy "
                    "words. Keep a steady musical cadence - every line is one short breath, a line break is a pause in "
                    "the voiceover. Write it so people feel seen and connected. The LAST TWO LINES are the strongest: "
                    "the ones people screenshot and send to someone."),
        "hook_styles": [
            "Begin the poem with the everyday moment itself, in one short line",
            "Begin with a question someone has whispered to themselves at night",
            "Begin with the ordinary thing that quietly holds the feeling",
            "Begin with a confession - one plain line, no drama",
        ],
        "ending_styles": [
            "End with a soft acceptance - the last two lines screenshot-worthy",
            "End by turning the ache into a quiet kindness",
            "End with a line people would want to send to someone",
        ],
        "themes": [
            "the one who says 'I'm fine' when they are not",
            "overthinking at 1am about a message that means nothing",
            "the child who still waits for a parent's loud love",
            "the friend who always gives and never asks",
            "a rented room at night and the whole city outside",
            "growing up away from home and learning to call a new place 'here'",
            "the last quiet morning of a love that had already ended",
            "the way you talk to yourself when no one is listening",
        ],
        "visual_modes": ["nostalgic_room", "bridge", "landscape", "female", "abstract_emotion", "friends_or_couple"],
        "voice": "soft_female",
    },
    {
        "format": "poem",
        "key": "HEALING_POEM",
        "name": "Poem (Healing)",
        "script": ("A gentle healing poem: it starts from the ache, walks through one small ordinary image, "
                    "and ends warm. The words must be plain - a friend speaking slowly at night, with a quiet "
                    "rhythmic cadence that lets people feel a real connection. No drama. The last three lines are "
                    "where the poem earns its 'save this' power."),
        "hook_styles": [
            "Begin with the ache in one plain line",
            "Begin with the night and how long it felt",
            "Begin with what broke, quietly, without drama",
            "Begin with the day the light came back, slowly",
        ],
        "ending_styles": [
            "End with the day it quietly got lighter",
            "End with permission - you are allowed to be gentle with yourself",
            "End by handing the ache back to the rain, warm",
        ],
        "themes": [
            "the slow return of light after a long dark season",
            "learning to be gentle with the version of you that broke",
            "the quiet strength in asking for help",
            "rebuilding yourself in small, ordinary ways",
            "grief that slowly became a softer room to carry",
            "forgiving yourself for surviving wrong",
            "the first morning you woke up and did not check the old messages",
        ],
        "visual_modes": ["landscape", "bridge", "nature", "abstract_emotion", "friends_or_couple", "object"],
        "voice": "warm_female",
    },
]

# ===========================================================================
# End of quarantined legacy fragment.
"""

# TIME BASED CONTENT MOOD (unchanged)
# ===========================================================================

TIME_SCHEDULE = {

"morning": {
    "start": 6,
    "end": 11,
    "mood": "positive reflection and personal growth"
},

"afternoon": {
    "start": 11,
    "end": 17,
    "mood": "reality checks and life lessons"
},

"evening": {
    "start": 17,
    "end": 22,
    "mood": "emotional and relatable truths"
},

"night": {
    "start": 22,
    "end": 6,   # Covers 22-24 and 0-6 (wraps around midnight)
    "mood": "deep thoughts and quiet reflections"
}

}


# ===========================================================================
# GET CURRENT TIME CATEGORY
# ===========================================================================

def get_content_type_for_time():

    hour = datetime.now().hour

    for category, data in TIME_SCHEDULE.items():
        start = data["start"]
        end = data["end"]

        # Handle wraparound for night (22-24 and 0-6)
        if start > end:  # Night wraps around midnight
            if hour >= start or hour < end:
                return {
                    "category": category,
                    "mood": data["mood"]
                }
        else:
            if start <= hour < end:
                return {
                    "category": category,
                    "mood": data["mood"]
                }

    # Fallback (should never reach here)
    return {
        "category": "night",
        "mood": "deep thoughts and quiet reflections"
    }


# ===========================================================================
# LAST SELECTED ARCHETYPE (read by story_generation / voice_generation)
# ===========================================================================

LAST_ARCHETYPE_INFO = None

# Full last selection (key/theme/hook/ending) so story_generation can pin a
# retry to the SAME archetype instead of re-picking and burning a slot.
LAST_PROMPT_SELECTION = None


def reset_tracker():
    """Clear the local no-repeat memory (for tests)."""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
    except OSError:
        pass


# ===========================================================================
# CREATE FINAL LLM PROMPT
# ===========================================================================

def _weighted_choice(items, weights):
    return random.choices(items, weights=weights, k=1)[0]


def _archetype_options(forced_format=None):
    if forced_format in ("poem", "prose"):
        return [a for a in ARCHETYPES if (a.get("format") == forced_format)]
    return list(ARCHETYPES)


def _pick_archetype(cache, forced_format=None):
    """Pick a varied archetype without making poem/prose predictable."""
    options = _archetype_options(forced_format)
    recent = cache.get("archetypes", [])[-4:]
    recent_formats = cache.get("formats", [])[-3:]
    weights = []
    for archetype in options:
        weight = 1
        if archetype["key"] in recent:
            weight = 0.15
        if len(recent_formats) >= 2 and all(
            value == archetype.get("format", "prose") for value in recent_formats[-2:]
        ):
            weight *= 0.25
        weights.append(weight)
    selected = _weighted_choice(options, weights)
    return selected["key"]


def _pick_from(values, recent, default):
    values = list(values or [default])
    candidates = [value for value in values if value not in recent[-2:]] or values
    return random.choice(candidates)


def _creative_profile(selected, cache):
    key = selected["key"]
    format_name = selected.get("format", "prose")
    defaults = {
        "MICRO_STORY": ("CONNECT", "SEND_TO_SOMEONE", "MICRO_STORY", "STORYTELLING", "MEDIUM", "micro_story"),
        "WISDOM_TRUTH": ("RETHINK", "REFLECTION", "OBSERVATIONAL", "SLOW", "MEDIUM", "short_reflection"),
        "REALITY_TALK": ("NOTICE", "YOU_NEED_THIS", "BOLD_TRUTH", "DIRECT", "MEDIUM", "advice"),
        "HOPE_AFTER": ("ENCOURAGE", "HOPE", "EMOTIONAL_REALIZATION", "SLOW", "MEDIUM", "short_reflection"),
        "LETTER_FORMAT": ("CONNECT", "SEND_TO_SOMEONE", "LETTER", "CONVERSATIONAL", "MEDIUM", "letter"),
        "DESI_SLICE": ("REMEMBER", "NOSTALGIA", "NOSTALGIA", "STORYTELLING", "LOW", "micro_story"),
        "JOY_QUIET": ("NOTICE", "WARMTH", "WARM", "SLOW", "LOW", "short_reflection"),
        "RELATABLE_POEM": ("RECOGNIZE", "IDENTIFICATION", "POEM", "RHYTHMIC", "MEDIUM", "poem"),
        "HEALING_POEM": ("COMFORT", "YOU_NEED_THIS", "POEM", "POETIC", "MEDIUM", "poem"),
    }
    purpose, intent, arc, pacing, temperature, creative_format = defaults.get(
        key, ("RECOGNIZE", "IDENTIFICATION", "NO_ARC", "CONVERSATIONAL", "MEDIUM", format_name)
    )
    format_name = selected.get("creative_format", creative_format)
    if selected.get("arc_options"):
        arc = _pick_from(selected["arc_options"], [item.get("arc") for item in cache.get("recent_dna", [])], arc)
    hook = _pick_from(
        selected.get("hook_behaviors") or HOOK_OPTIONS_BY_KEY.get(key),
        [item.get("hook_style") for item in cache.get("recent_dna", [])],
        "CONFESSION",
    )
    ending = _pick_from(
        selected.get("ending_behaviors") or ENDING_OPTIONS_BY_KEY.get(key),
        [item.get("ending_style") for item in cache.get("recent_dna", [])],
        "UNDERSTATED_ENDING",
    )
    return {
        "purpose": purpose,
        "intent": intent,
        "pillar": _pick_from(
            selected.get("pillar_options") or PILLAR_OPTIONS_BY_KEY.get(key),
            [item.get("pillar") for item in cache.get("recent_dna", [])],
            key,
        ),
        "format": format_name,
        "arc": arc,
        "hook_style": hook,
        "ending_style": ending,
        "pacing": pacing,
        "temperature": temperature,
        "word_range": FORMAT_RANGES.get(format_name, (80, 110)),
        "detail_hint": random.choice(EVERYDAY_DETAILS),
    }


def get_prompt_for_current_time(pinned=None, story_payload=None):
    """
    Build the full Gemini prompt for today's reel.

    Picks an archetype while alternating poem/prose 1-after-1 (no same format
    twice in a row), a theme (no repeats within the last few), a hook style,
    an ending style, the time-of-day mood and the weekday energy. Sets
    LAST_ARCHETYPE_INFO so the rest of the pipeline (visual mode, voice) can
    stay consistent with the chosen archetype.

    pinned: optional dict from LAST_PROMPT_SELECTION. When provided (retry
    path), the EXACT same archetype/theme/hook/ending is reused and the
    no-repeat tracker is left untouched, so a retry never burns a slot or
    breaks the poem/prose alternation.

    story_payload: optional returned story used to store the chosen hook line
    so future reels stay unique.
    """
    global LAST_ARCHETYPE_INFO, LAST_PROMPT_SELECTION

    content = get_content_type_for_time()
    weekday_label, weekday_direction = get_weekday_direction()
    hook_history = _load_hook_history()
    cache = _load_cache()

    if pinned is not None:
        content = pinned.get("time_context", content)
        weekday_label = pinned.get("weekday_label", weekday_label)
        weekday_direction = pinned.get("weekday_direction", weekday_direction)
        selected_key = pinned["key"]
        selected = next(a for a in ARCHETYPES if a["key"] == selected_key)
        theme = pinned.get("theme", selected["themes"][0])
        profile = pinned.get("profile") or _creative_profile(selected, cache)
        hook_instruction = pinned.get("hook_instruction", HOOK_BEHAVIORS.get(profile["hook_style"], profile["hook_style"]))
        recent_hooks_block = _format_recent_hooks(hook_history, pinned.get("hook_block"))
    else:
        forced = os.getenv("FORCE_REEL_FORMAT", "").strip().lower()
        forced = forced if forced in ("poem", "prose") else None

        selected_key = _pick_archetype(cache, forced_format=forced)
        selected = next(a for a in ARCHETYPES if a["key"] == selected_key)

        theme = _pick_no_repeat(selected["themes"], "themes", cache, history_len=5)
        profile = _creative_profile(selected, cache)
        hook_instruction = HOOK_BEHAVIORS.get(profile["hook_style"], random.choice(selected["hook_styles"]))

        recent_hooks_block = _format_recent_hooks(hook_history)

        cache.setdefault("archetypes", []).append(selected_key)
        cache["archetypes"] = cache["archetypes"][-12:]
        cache.setdefault("themes", []).append(theme)
        cache["themes"] = cache["themes"][-12:]
        cache.setdefault("formats", []).append(profile["format"])
        cache["formats"] = cache["formats"][-12:]
        cache.setdefault("recent_dna", []).append({"theme": theme, **profile})
        cache["recent_dna"] = cache["recent_dna"][-10:]
        _save_cache(cache)

        LAST_PROMPT_SELECTION = {
            "key": selected_key,
            "theme": theme,
            "hook_instruction": hook_instruction,
            "profile": profile,
            "hook_block": recent_hooks_block,
            "time_context": content,
            "weekday_label": weekday_label,
            "weekday_direction": weekday_direction,
        }

    LAST_ARCHETYPE_INFO = {
        "key": selected["key"],
        "name": selected["name"],
        "format": selected.get("format", "prose"),
        "theme": theme,
        **profile,
        "visual_modes": selected["visual_modes"],
        "voice": selected["voice"],
        "weekday": weekday_label,
    }

    print(f"\n🎭 Reel archetype: {selected['name']} ({selected['key']} / {selected.get('format', 'prose')})")
    print(f"💡 Theme: {theme}")
    print(f"🗣️ Voice profile: {selected['voice']}")
    print(f"🎯 Purpose/intent: {profile['purpose']} / {profile['intent']}")
    print(f"🧩 Creative DNA: {profile['format']} / {profile['arc']} / {profile['pacing']}")

    final_prompt = f"""
{BASE_INSTRUCTION}


==================================================
TODAY'S REEL GENERATOR - READ ALL OF IT
==================================================

STORY TYPE:
{selected['name']}
{selected['script']}


CONTENT PURPOSE:
{profile['purpose']} - {CONTENT_PURPOSES.get(profile['purpose'], '')}

VIEWER INTENT:
{profile['intent']} - {VIEWER_INTENTS.get(profile['intent'], '')}

CONTENT PILLAR:
{profile['pillar']}

CREATIVE ARC:
{profile['arc']} - {CREATIVE_ARCS.get(profile['arc'], '')}

FORMAT AND LENGTH:
{profile['format']} - write between {profile['word_range'][0]} and {profile['word_range'][1]} words so the downstream compatibility validator can accept it.

PACING:
{profile['pacing']} - {PACING_STYLES.get(profile['pacing'], '')}

CREATIVE TEMPERATURE:
{profile['temperature']} - {CREATIVE_TEMPERATURES[profile['temperature']]}

OPTIONAL DETAIL POOL:
If a physical detail improves this idea, choose one naturally from this kind of world: {profile['detail_hint']}. Do not add it merely because it appears here.


THEME / MOMENT TO WRITE ABOUT:
{theme}


HOOK BEHAVIOR:
{profile['hook_style']} - {hook_instruction}

HOOK UNIQUENESS – READ CAREFULLY:
The hook must be short, fresh, unique, and relatable – never a line that has
appeared before. Do NOT reuse phrases from these recent hooks or write close
paraphrases of them:
{recent_hooks_block}

RULES FOR THIS HOOK:
- Let the selected hook behavior decide the length and shape. It may be a short phrase, a full sentence, a question, dialogue, or a scene line.
- Make it fresh and fitted to this reel, not a generic quote-card slogan.
- DO NOT use the same opening line as the narration below.
- DO NOT quote the narration's first spoken line.
- A fresh visual metaphor is welcome, but avoid overused reels language.
- If a draft matches any of the recent hooks above in words, rhythm, or idea,
  discard it and write a stronger, completely different one.


ENDING BEHAVIOR:
{profile['ending_style']} - {ENDING_BEHAVIORS.get(profile['ending_style'], '')}


TIME-OF-DAY SUGGESTION (LOW WEIGHT; CONTENT MAY IGNORE IT):
{content['mood']}


WEEKDAY SUGGESTION (LOW WEIGHT; CONTENT MAY IGNORE IT):
{weekday_label} - {weekday_direction}


==================================================
WRITING THIS REEL

- Write one voiceover in the selected format and word range.
- Follow the selected creative direction naturally. Do not force a turn, object,
    short punch line, or strongest final line unless the selected arc or ending
    calls for it.
- The narration should sound complete even if the background video is removed.

{KICK_ENGINE}
- If the story type is a letter, write it as a short intimate letter.
- If the story type is a POEM, write a short RHYTHMIC free-verse poem in the
  simplest everyday words: each line is one short breath with a steady musical
-  cadence (line breaks = subtitle pauses). Do not force the last lines to be
    stronger than the rest unless the selected ending calls for that.
- Keep it simple, specific, and shareable. No cliches, no motivational-speaker tone.
- The six visual scenes will be built from your narration, so make the
  narration visual enough to paint (a moment, a place, a gesture, light, rain).

==================================================
FINAL CREATIVE CHECK (SILENT)
==================================================
Before returning, ask:
1. Does this sound like a real human thought rather than a reel template?
2. Is there a specific idea, even if there is no object or twist?
3. Am I forcing a turn, object, punch line, or huge ending?
4. Does the hook fit this story and the selected viewer intent?
5. Is the ending natural for this format?
6. Could someone recognize themselves or send this to one person?
7. Would it still be interesting without the background video?
8. Does it sound like one of the recent reels? If yes, rewrite it.
"""

    return final_prompt


# ===========================================================================
# TEST
# ===========================================================================

if __name__ == "__main__":
    print(get_prompt_for_current_time())

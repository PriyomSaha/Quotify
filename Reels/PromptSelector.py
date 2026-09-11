"""
Reels/PromptSelector.py

Reel narration prompt builder for "Aesthetic Vibes" - V2 diversity overhaul.

Changes:
- 9 rotating Reel archetypes (7 prose + 2 po-em) so every reel is structurally different.
- Poems alternate with prose reels 1-after-1 (poem -> prose -> poem -> ...).
- Per-archetype themes, hook styles, ending styles, visual modes and voice.
- Memory guard (no recent repeats) persisted in a local cache file.
- Emotional arc (tension -> recognition -> payoff) + sensory/desi detail rule.
- hook_line + caption instructions for the caption and video composer.
- Word count unified to 80-110 (matches story_generation.py validation).
"""

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
    try:
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return {"archetypes": [], "themes": []}


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

EMOTIONAL ARC - every piece must travel three beats:
1. TENSION - the first 1-2 lines establish something at stake: a truth, a loss, a contradiction, a feeling held too long.
2. RECOGNITION - one specific everyday detail that makes the viewer think "that's exactly me."
3. PAYOFF - the last 1-2 lines are the strongest thought: worth saving, screen captioning, or sending to someone.

ALWAYS include at least ONE sensory or desi detail somewhere, and ROTATE which one - do not use rain in every reel: chai steam rising, a phone ringing at the wrong hour, the smell of home-cooked food, morning light through a window, a bus window in motion, a mother's voice, a street dog at the gate, dust dancing in sunlight, the whistle of a pressure cooker, a train pulling in, the hum of a ceiling fan, a cold breeze off a river, an auto-rickshaw ride, the first bite of something familiar, footsteps on a quiet staircase. Make it feel lived, not invented.

HOOK RULES (the first line must stop the scroll):
- 4-9 words, curiosity or emotion in under 2 seconds.
- Use the today's hook style.
- Never start with "Sometimes", "People", or "Life" every time.
- Start mid-feeling, not with a setup.

LENGTH (hard rule):
- Between 80 and 110 words total. The API enforces this.

SAFETY - always:
- No names that are not obviously ordinary, no celebrities.
- No politics, religion debates, hate, or violence.
- Keep it original. Never copy songs, poems, speeches or famous quotes.
- Be gentle. Hard truths are okay; cruelty is not.
"""


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

ARCHETYPES = [
    {
        "format": "prose",
        "key": "MICRO_STORY",
        "name": "Micro Story",
        "script": ("ONE specific everyday moment that could truly have happened, told like a memory: "
                    "a phone call, a bus ride, a night of silence, a quiet goodbye. "
                    "Tell it scene by scene; the story makes the truth; the last line is that truth."),
        "hook_styles": [
            "Start with the moment itself (e.g. That night my father called just to hear my voice)",
            "Start with one small gesture that carried meaning",
            "Start with a place and a time (e.g. Last winter, at the metro gate)",
            "Start with a journal-style line about that specific night",
        ],
        "ending_styles": [
            "End with the quiet truth the moment pointed to",
            "End with what you would tell that person now",
            "End warm and human, not dramatic",
        ],
        "themes": [
            "a parent's repeated phone call you almost ignored",
            "a goodbye said casually that stayed forever",
            "the last bus home after everything changed",
            "a friend's voice after years of silence",
            "a small habit that quietly saved a hard month",
        ],
        "visual_modes": ["bridge", "nostalgic_room", "female", "male", "landscape", "friends_or_couple"],
        "voice": "deep_male",
    },
    {
        "format": "prose",
        "key": "WISDOM_TRUTH",
        "name": "Wisdom Truth",
        "script": "A calm, universal truth someone learns from living. No story characters, one central idea that unfolds line by line and lands in a shareable last line.",
        "hook_styles": [
            "Start with a quiet realization",
            "Start with a thought that sounds like a journal entry",
            "Start with something only experience teaches",
            "Start with a contradiction that resolves itself",
        ],
        "ending_styles": [
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
        "script": ("A short free-verse poem in the SIMPLEST everyday words about a feeling almost everyone has lived: "
                    "the one who says 'I'm fine', overthinking at 1am, the daughter still seeking a parent's approval, "
                    "the person in a rented room far from home, the friend who always gives. No big metaphors, no heavy "
                    "words. Every line is one short breath - a line break is a pause in the voiceover. The LAST TWO "
                    "LINES are the strongest: the ones people screenshot and send to someone."),
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
                    "and ends warm. The words must be plain - a friend speaking slowly at night. No rhymes forced, "
                    "no drama. The last three lines are where the poem earns its 'save this' power."),
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

def _pick_archetype(cache, forced_format=None):
    """
    Alternate poem/prose 1-after-1 so the feed never shows the same format
    twice in a row (poem -> prose -> poem -> prose ...), with no-repeat
    inside each pool as well. Writes the chosen format back into cache.

    forced_format ("poem"/"prose") overrides alternation for one run, e.g.
    when the user explicitly wants a poem next: FORCE_REEL_FORMAT=poem.
    """
    poem_keys = [a["key"] for a in ARCHETYPES if a.get("format") == "poem"]
    prose_keys = [a["key"] for a in ARCHETYPES if a.get("format") != "poem"]

    # Strict 1-after-1 alternation: if last was a poem, pick prose (and vice versa)
    if forced_format == "poem":
        pool = poem_keys
    elif forced_format == "prose":
        pool = prose_keys
    elif cache.get("last_format") == "poem":
        pool = prose_keys
    else:
        pool = poem_keys

    history = cache.get("archetypes", [])
    recent = [h for h in history[-2:] if h in pool]
    candidates = [k for k in pool if k not in recent]
    if not candidates:
        candidates = list(pool)

    key = random.choice(candidates)
    cache["last_format"] = "poem" if key in poem_keys else "prose"
    return key


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
        selected_key = pinned["key"]
        selected = next(a for a in ARCHETYPES if a["key"] == selected_key)
        theme = pinned["theme"]
        hook = pinned["hook"]
        ending = pinned["ending"]
        hook_instruction = pinned.get("hook_instruction", hook)
        recent_hooks_block = _format_recent_hooks(hook_history, pinned.get("hook_block"))
    else:
        forced = os.getenv("FORCE_REEL_FORMAT", "").strip().lower()
        forced = forced if forced in ("poem", "prose") else None

        selected_key = _pick_archetype(cache, forced_format=forced)
        selected = next(a for a in ARCHETYPES if a["key"] == selected_key)

        theme = _pick_no_repeat(selected["themes"], "themes", cache, history_len=5)
        hook = random.choice(selected["hook_styles"])
        ending = random.choice(selected["ending_styles"])
        hook_instruction = hook

        # Build the do-not-repeat block ONCE and store it, so the retry
        # path reuses the exact same text (identical prompt).
        recent_hooks_block = _format_recent_hooks(hook_history)

        # Update local memory
        cache.setdefault("archetypes", []).append(selected_key)
        cache["archetypes"] = cache["archetypes"][-12:]
        cache.setdefault("themes", []).append(theme)
        cache["themes"] = cache["themes"][-12:]
        _save_cache(cache)

        # Remember the full selection so a retry can pin the identical prompt
        LAST_PROMPT_SELECTION = {
            "key": selected_key,
            "theme": theme,
            "hook": hook,
            "hook_instruction": hook_instruction,
            "ending": ending,
            "hook_block": recent_hooks_block,
        }

    LAST_ARCHETYPE_INFO = {
        "key": selected["key"],
        "name": selected["name"],
        "format": selected.get("format", "prose"),
        "theme": theme,
        "visual_modes": selected["visual_modes"],
        "voice": selected["voice"],
        "weekday": weekday_label,
    }

    print(f"\n🎭 Reel archetype: {selected['name']} ({selected['key']} / {selected.get('format', 'prose')})")
    print(f"💡 Theme: {theme}")
    print(f"🗣️ Voice profile: {selected['voice']}")

    final_prompt = f"""
{BASE_INSTRUCTION}


==================================================
TODAY'S REEL GENERATOR - READ ALL OF IT
==================================================

STORY TYPE:
{selected['name']}
{selected['script']}


THEME / MOMENT TO WRITE ABOUT:
{theme}


HOOK STYLE (first line must follow this):
{hook_instruction}

HOOK UNIQUENESS – READ CAREFULLY:
The hook must be short, fresh, unique, and relatable – never a line that has
appeared before. Do NOT reuse phrases from these recent hooks or write close
paraphrases of them:
{recent_hooks_block}

RULES FOR THIS HOOK:
- 1-2 short lines maximum; each line UNDER 45 characters including spaces.
- Original, concrete, emotional, and in three or fewer short beats.
- DO NOT use the same opening line as the narration below.
- DO NOT quote the narration's first spoken line.
- A fresh visual metaphor is welcome, but avoid overused reels language.
- If a draft matches any of the recent hooks above in words, rhythm, or idea,
  discard it and write a stronger, completely different one.


ENDING STYLE:
{ending}


TIME-OF-DAY MOOD:
{content['mood']}


WEEKDAY FEEL:
{weekday_label} - {weekday_direction}


==================================================
WRITING THIS REEL

- Write ONE reel voiceover, 80 to 110 words, line by line.
- Follow the emotional arc: tension -> recognition -> payoff.
- End on the strongest line. Do not explain after it.
- If the story type is a letter, write it as a short intimate letter.
- If the story type is a POEM, write a short free-verse poem in the simplest
  everyday words: each line is one short breath (line breaks = subtitle
  pauses), no forced rhymes, and the LAST TWO LINES are the strongest -
  the ones people screenshot and send.
- Keep it simple, specific, and shareable. No cliches, no motivational-speaker tone.
- The six visual scenes will be built from your narration, so make the
  narration visual enough to paint (a moment, a place, a gesture, light, rain).
"""

    return final_prompt


# ===========================================================================
# TEST
# ===========================================================================

if __name__ == "__main__":
    print(get_prompt_for_current_time())

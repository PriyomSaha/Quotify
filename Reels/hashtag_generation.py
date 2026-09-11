import random
from typing import Optional, Dict, Any

from event_detector import build_event_caption_prefix, get_event_hashtags

# Always included (brand + niche anchors)
FIXED_HASHTAGS = [
    "#AestheticVibes",
    "#LifeQuotes",
    "#LifeLessons"
]

# Curated niche pool - relevance >> spam. These are the tags that actually
# carry your real audience (South Asian, healing, deep-thoughts) into
# saves/shares/explore. The old pool's "#Viral/#Explore/#Trending" spam
# actively hurts niche relevance signals, so it is no longer used.
NICHE_HASHTAGS = [
    "#deepthoughts",
    "#healingjourney",
    "#innerpeace",
    "#selflove",
    "#selflovejourney",
    "#selfcare",
    "#mentalhealthmatters",
    "#mentalwellness",
    "#soulfulvibes",
    "#emotional",
    "#deepfeelings",
    "#relatable",
    "#relatablequotes",
    "#quotestoliveby",
    "#quotestoremember",
    "#wordsforwomen",
    "#wordsforher",
    "#southasiangirls",
    "#southasiancreator",
    "#desilife",
    "#desicontent",
    "#monsoonvibes",
    "#chaiandthoughts",
    "#desivibes",
    "#reelsindia",
    "#reelsinstagram",
    "#quietreflections",
    "#healingmind",
    "#wordsfromtheheart",
    "#southasianstories",
    "#morningquotes",
    "#growthjourney",
    "#lettinggo",
    "#boundaries",
    "#mindset",
    "#calmquotes",
    "#quietmoments",
    "#dailyquotes",
    "#quoteoftheday",
]

def generate_hashtags(
    min_count=8,
    max_count=12,
    event: Optional[Dict[str, Any]] = None,
):
    """
    Returns a string of 8-12 niche-first hashtags.

    Always includes the fixed brand anchors, then fills from the curated
    # niche pool.
    pool. The old 20-23 tag spam (including #Viral / #Explore / #Trending) is
    gone - 8-12 relevant tags perform better for saves, shares and explore.
    """

    event_tags = get_event_hashtags(event)
    fixed_tags = list(dict.fromkeys(FIXED_HASHTAGS + event_tags))

    if min_count < len(fixed_tags):
        min_count = len(fixed_tags)

    if max_count < min_count:
        max_count = min_count

    total = random.randint(min_count, max_count)
    available_pool = [tag for tag in NICHE_HASHTAGS if tag not in fixed_tags]
    random_count = min(total - len(fixed_tags), len(available_pool))

    random_tags = random.sample(
        available_pool,
        random_count
    )

    hashtags = fixed_tags + random_tags
    random.shuffle(hashtags)

    return " ".join(hashtags)


# ---------------------------------------------------------------------------
# CTA BANK - rotate so the feed never asks the same call twice
# ---------------------------------------------------------------------------

CTA_BANK = [
    "Save this for the day you need it.",
    "Send this to someone who needs to hear it.",
    "What did this bring back for you?",
    "Who does this sound like? Share it with them.",
    "Paste this where you keep the words that matter.",
    "If this found you, it was meant to find you.",
    "Comment your own story - this community reads every word.",
    "Tag the friend you grew up with the most.",
    "Read it once. Then read it again, slowly.",
    "Which line stayed with you? Drop it below.",
]


def build_reel_caption(
    title: str = "",
    fallback_text: str = "",
    max_title_chars: int = 300,
    event: Optional[Dict[str, Any]] = None,
    story: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a Meta-safe reel caption with:
      1st line: the strongest line (hook_line > caption_line > title)
      2nd: a rotating soft call-to-action (or the story's own CTA)
      3rd: 8-12 niche hashtags

    Keeps only clean line breaks between blocks.
    """
    story = story or {}
    hook_line = (story.get("hook_line") or "").strip()
    caps = story.get("captions")
    if not isinstance(caps, dict):
        caps = {}
    caption_line = (caps.get("caption_line") or "").strip()
    cta = (caps.get("cta") or "").strip()
    cta = cta or random.choice(CTA_BANK)

    first_line = (
        hook_line or caption_line or title or fallback_text or "Aesthetic Vibes"
    )
    first_line = " ".join(first_line.split())[:max_title_chars].strip()

    event_prefix = build_event_caption_prefix(event)
    if event_prefix and event_prefix.lower() not in first_line.lower():
        first_line = f"{event_prefix}: {first_line}"

    hashtags = generate_hashtags(event=event).strip()

    return f"{first_line}\n\n{cta}\n\n{hashtags}"


if __name__ == "__main__":
    print(generate_hashtags())
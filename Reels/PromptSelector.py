import random
from datetime import datetime


# ============================================================
# CORE WRITING INSTRUCTION
# ============================================================

BASE_INSTRUCTION = """

You write short viral wisdom voiceovers for Instagram Reels.

Your content is NOT a story.

Do NOT create:
- characters
- names
- places
- events
- conversations
- fictional situations

Write like a person sharing a deep truth they learned from life.

The viewer should feel:
"I needed to hear this."

STYLE:

- Simple English
- Mature and calm tone
- Deep meaning with few words
- Emotional but controlled
- Easy to understand
- Natural spoken language

FORMAT:

Every sentence must be on a separate line.

Use line breaks as breathing pauses.

Example:

People change...

Sometimes the person who values you today...

May become the person who ignores you tomorrow.

That is why...

Never lose yourself trying to keep someone else.


WRITING PATTERNS:

Use different styles:

1. Personal realization:

"I trusted people too easily..."

"I gave chances they never deserved..."


2. Life advice:

"Let people misunderstand you..."

"Time reveals what words cannot..."


3. Hard truth:

"Nobody talks about this..."

"Some lessons only come after losing something..."


4. Emotional reflection:

"Sometimes you don't miss the person..."

"You miss who they used to be..."


HOOK RULES:

The first line must stop scrolling.

Use different opening styles:

- Truth is...
- Remember this...
- Nobody talks about this...
- One day you will understand...
- Learn this early...
- The hardest lesson in life...
- Stop doing this...
- Accept this...
- A painful truth is...


ENDING RULES:

The last 2-3 lines must contain the strongest thought.

Rotate endings:

- painful realization
- life lesson
- self respect reminder
- acceptance
- emotional truth
- peaceful conclusion


IMPORTANT:

Do not sound like a motivational speaker.

Do not use:
- "You can do anything"
- "Never give up"
- "Everything happens for a reason"

Avoid clichés.

Length:
40-90 words.

Tone:
A calm person sharing wisdom after experiencing life.


# ============================================================
# VARIETY
# ============================================================

Keep the existing style, quality, and tone.

Do not make every piece follow the same structure.

Vary the opening and rhythm naturally:
- observation
- realization
- question
- direct thought
- contradiction
- poetic line
- relatable feeling
- unexpected comparison
- quiet reflection

Existing hooks are still allowed, including:
"A painful truth is..."
"Nobody talks about this..."
"Remember this..."

Use them occasionally rather than repeatedly.

Some pieces may feel like a short modern free-verse poem.

Poems should be:
- simple
- emotional
- conversational
- modern
- easy to understand
- free of forced rhymes

Do not make every piece sound like a motivational speech.

Let some thoughts build slowly and others be direct.

Do not force every sentence to sound profound.

"""


# ============================================================
# CONTENT THEMES
# ============================================================

THEMES = [

"hard truths about life",

"people changing over time",

"learning to stand alone",

"protecting your peace",

"self respect and boundaries",

"trusting people too much",

"fake friendships",

"silent struggles nobody sees",

"being taken for granted",

"expectations and disappointment",

"letting people go",

"accepting change",

"emotional maturity",

"healing after pain",

"forgiving but remembering",

"choosing yourself",

"life lessons learned late",

"human nature",

"relationships and distance",

"things people realize too late",

"success and sacrifice",

"loneliness and growth",

"patience and timing",

"not explaining yourself",

"finding peace"

]


# ============================================================
# HOOK STYLES
# ============================================================

HOOK_STYLES = [

"Start with a hard truth",

"Start with a surprising observation",

"Start with a direct advice",

"Start with a painful realization",

"Start with a question",

"Start with a statement people relate to",

# Additional variety — existing hooks above are intentionally kept

"Start with a quiet realization",

"Start with an unexpected observation",

"Start with something people usually understand with age",

"Start with a simple thought that becomes deeper as it continues",

"Start with a thought about something we often take for granted",

"Start with a relatable feeling",

"Start with a contradiction",

"Start with two things that seem opposite but are both true",

"Start with a short poetic line",

"Start with a metaphor about life",

"Start with a thought that sounds like a journal entry",

"Start with something the viewer may have felt but never said",

"Start with a subtle observation about human nature",

"Start with a question that makes the viewer look inward",

"Start with a sentence that creates curiosity without explaining everything",

"Start with a very short statement",

"Start with a quiet thought rather than direct advice",

"Start with an observation about time",

"Start with an observation about growing older",

"Start with an unexpected comparison",

"Start with a realization that unfolds gradually",

"Start with a thought about something we usually notice too late",

"Start with a simple statement that carries a deeper meaning",

"Start with a thought that feels like the beginning of a personal journal entry",

"Start with a line that creates curiosity without sounding dramatic"

]


# ============================================================
# ENDING STYLES
# ============================================================

ENDING_STYLES = [

"End with a powerful life lesson",

"End with self respect",

"End with acceptance",

"End with a painful truth",

"End with emotional reflection",

"End with a peaceful realization"

]


# ============================================================
# CONTENT FORMATS
# ============================================================

CONTENT_FORMATS = [

# Normal style — intentionally dominant
"wisdom voiceover",
"wisdom voiceover",
"wisdom voiceover",
"wisdom voiceover",

"life reflection",

"life observation",

"hard truth",

"emotional reflection",

"personal realization",

"quiet realization",

"philosophical reflection",

# Occasional poetic styles
"short free verse poem",

"poetic reflection",

"minimalist poem",

"short modern poem"

]


# ============================================================
# ADDITIONAL CONTENT DIRECTIONS
# ============================================================

# These are small directions rather than completely different formats.
# They help prevent the generated pieces from following one repeated
# structure while keeping the original style intact.

CONTENT_DIRECTIONS = [

"Build the thought gradually",

"Keep it direct and conversational",

"Let the meaning unfold naturally",

"Use a quiet emotional tone",

"Use a subtle contrast",

"Focus on one clear realization",

"Make the thought feel relatable",

"Keep the language simple but meaningful",

"Use a slightly poetic rhythm",

"Make the ending feel earned rather than forced",

"Use short lines for breathing pauses",

"Let one sentence carry the central idea",

"Keep the emotion controlled and mature",

"Make it feel like a thought someone had after living through something",

"Leave a little space for the viewer to interpret the meaning"

]


# ============================================================
# TIME BASED CONTENT MOOD
# ============================================================

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
    "end": 6,  # Covers 22-24 and 0-6 (wraps around midnight)
    "mood": "deep thoughts and quiet reflections"
}

}


# ============================================================
# GET CURRENT TIME CATEGORY
# ============================================================

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



# ============================================================
# CREATE FINAL LLM PROMPT
# ============================================================

def get_prompt_for_current_time():

    content = get_content_type_for_time()

    theme = random.choice(THEMES)

    hook = random.choice(HOOK_STYLES)

    ending = random.choice(ENDING_STYLES)

    content_format = random.choice(CONTENT_FORMATS)

    content_direction = random.choice(CONTENT_DIRECTIONS)

    final_prompt = f"""

{BASE_INSTRUCTION}


TODAY'S CONTENT DIRECTION:

Theme:
{theme}


Mood:
{content['mood']}


Hook Style:
{hook}


Ending Style:
{ending}


Content Format:
{content_format}


Writing Direction:
{content_direction}



Generate ONE short wisdom reel voiceover.

The selected content format and writing direction are guidelines, not rigid templates.

If the format is a poem, write it as a short modern free-verse poem while keeping the same wisdom, simplicity, and emotional tone.

Remember:

No story.
No characters.
No explanation.

Only a powerful thought written line by line.

"""


    return final_prompt



# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(get_prompt_for_current_time())
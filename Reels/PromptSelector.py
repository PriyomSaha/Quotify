# ============================================================
# prompt_selector.py
# AI Wisdom Reel Prompt Selector
# ============================================================

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

"Start with a statement people relate to"

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
    "end": 24,
    "mood": "deep thoughts and quiet reflections"
}

}


# ============================================================
# GET CURRENT TIME CATEGORY
# ============================================================

def get_content_type_for_time():

    hour = datetime.now().hour

    for category, data in TIME_SCHEDULE.items():

        if data["start"] <= hour < data["end"]:
            return {
                "category": category,
                "mood": data["mood"]
            }


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



Generate ONE short wisdom reel voiceover.

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
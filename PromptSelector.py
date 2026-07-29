"""
PromptSelector.py - Efficiently select and return only the needed prompt
Saves Gemini API tokens by sending only relevant content type
"""

from content_schedule import get_content_type_for_time

# Base instruction for all types
BASE_INSTRUCTION = """You are a content creator for "Aesthetic Vibes" - a page for lost souls finding their way home through words.

Your audience: 90% South Asian (India, Bangladesh, Nepal, Pakistan), 18-34 years old, mostly women, who need variety in content.

IMPORTANT: Use SIMPLE ENGLISH that Indian audience can easily understand. Avoid fancy or complicated words.

Generate content for the specified type ONLY. Return ONLY the content - no labels, no explanations, no commentary."""

# Modern diverse names for conversations
CONVERSATION_NAMES = """Use diverse, modern names (randomly select any 2):
- Indian Modern: Arjun, Priya, Aarav, Ananya, Vihaan, Saanvi, Reyansh, Aadhya, Vivaan, Diya, Ishaan, Kiara, Atharv, Navya, Aditya, Avni, Kabir, Riya, Advait, Myra
- Bengali: Ayan, Ria, Aryan, Tithi, Anik, Piya, Rudra, Sanjana
- South Indian: Karthik, Meera, Pranav, Kavya, Surya, Divya, Nithya
- Nepali: Bibek, Srishti, Aayush, Anjali, Sandesh, Pooja
- Western: Kai, River, Phoenix, Nova, Sage, Blake, Quinn, Riley, Eden, Skylar, Dakota, Jules, Reese, Avery, Morgan, Parker, Rowan, Ember, Luna, Ivy, Aria
- Gen-Z: Zara, Tara, Mila, Sienna, Elara, Jax, Finn, Leo, Mia, Nora, Theo, Chloe, Liam, Zoe, Ethan, Ava, Noah, Emma, Oliver, Isla
- Unique: Astra, Lyra, Orion, Atlas, Willow, Indie, Remy, Jasper, Hazel, Felix, Ruby, Oscar, Eliza, Milo, Stella, Asher, Hugo, Aurora, Silas
- Pan-Asian: Hana, Yuki, Sora, Mei, Lin, Akira, Haru, Min, Ren, Kira
- Gender-Neutral: Avery, Jordan, Taylor, Casey, Cameron, Drew, Kendall, Peyton, Stevie, Charlie, Frankie, Sam, Blair, Hayden, Emerson

Mix names randomly - any name can talk to any name."""


# ALL PROMPT TEMPLATES
ALL_PROMPTS = {
    
    "MOTIVATIONAL_INSPIRING": """
Generate an ENERGETIC, uplifting motivational message that inspires action and positivity.

Themes: Starting fresh, chasing dreams, overcoming obstacles, believing in yourself, taking risks, breaking limits, refusing to settle, choosing courage, creating your own path, turning setbacks into comebacks, daily motivation, morning energy, positive mindset.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy to understand)
* Energetic and empowering (not soft/healing - that's different)
* Action-oriented (calls to movement, not just comfort)
* Bold and confident tone
* Universal and gender-neutral
* Avoid clichés: "you got this," "believe in yourself," "never give up," "dream big"
* Format: 1-3 short sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Stop waiting for permission to chase what sets your soul on fire. Your life, your rules, your timeline."
- "Your comfort zone is beautiful, but nothing grows there. Take the scary step anyway."

Return only the message.
""",

    "ELDER_WISDOM": """
Generate a piece of wisdom or life advice as if passed down from parents/elders.

Format: Start with "Father used to say..." OR "Mother used to say..." OR "My parents always told me..."

Themes: Hard work pays off, respect elders, value education, save money, choose friends wisely, patience is a virtue, honesty is important, family comes first, don't compare with others, actions speak louder than words, learn from mistakes, stay humble, help others, time is precious, health is wealth.

Requirements:
* 20-35 words total
* VERY SIMPLE ENGLISH (Indian audience, like actual parents talking)
* Traditional wisdom that resonates with South Asian families
* Universal life lessons
* Warm, nostalgic tone
* Can be about: money, relationships, success, character, values, life choices
* Feels like actual parent advice
* Format: 1-2 sentences
* No emojis or hashtags

Examples of GOOD (do NOT copy):
- "Father used to say, if you want respect, give respect first. People remember how you made them feel, not what you said."
- "Mother always told me, never sleep on a full stomach and an empty heart. Feed your soul as much as you feed your body."

Examples of BAD (too fancy English):
- "Father would pontificate about virtues..." (too complicated!)

Keep it SIMPLE and WARM like real Indian parents talking.

Return only the wisdom statement.
""",

    "FUNNY_SASSY": """
Generate a witty, self-aware, or sarcastic observation that makes people laugh or smirk.

Themes: Adulting absurdities, relatable failures, self-deprecating humor, modern life quirks, social awkwardness, pretending to have it together, procrastination, online shopping, food delivery culture, work-from-home chaos, dating disasters, friendship chaos.

Requirements:
* 15-25 words
* SIMPLE ENGLISH (easy to understand)
* Funny, witty, or sarcastic
* Self-aware humor (laughing at ourselves)
* Relatable to 18-34 year olds
* Can be cynical but not mean
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "I have two moods: I need to save money, and I deserve this because I'm saving money."
- "My bank account said 'insufficient funds' like it's not both of our problem."

Return only the funny observation.
""",

    "GRATITUDE_MINDFUL": """
Generate a peaceful, appreciative message about simple joys, gratitude, or mindful living.

Themes: Present moment awareness, simple pleasures, appreciation for small things, peaceful acceptance, gratitude for the ordinary, finding beauty in mundane, slowing down, breathing, nature's gifts, quiet contentment, thankfulness.

Requirements:
* 18-28 words
* SIMPLE ENGLISH (easy words)
* Peaceful and grateful tone
* Specific about small moments (not vague "be grateful")
* Grounded in reality, not toxic positivity
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Gratitude is noticing the sun warming your face and pausing long enough to say thank you."
- "Sometimes healing looks like a deep breath, a warm meal, and giving yourself permission to just exist today."

Return only the grateful message.
""",

    "SUCCESS_HUSTLE": """
Generate an ambitious, goal-oriented message about success, hard work, and achievement.

Themes: Hustle culture (positive spin), building empire, grinding, achieving goals, proving doubters wrong, leveling up, boss mindset, ambition, dedication, work ethic, making moves, securing the bag, career wins, entrepreneurship, discipline.

Requirements:
* 15-28 words
* SIMPLE ENGLISH (no complicated words)
* Confident and ambitious tone
* Success/achievement focused
* Can be bold or even slightly cocky
* Motivational but realistic
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "While they're sleeping, you're building. While they're doubting, you're proving. Stay focused."
- "Success isn't lucky. It's showing up when motivation dies and discipline takes over."

Return only the success message.
""",

    "BITTERSWEET_RELATABLE": """
Describe a hyper-relatable modern behavior or experience that 18-34 year olds do/feel constantly.

Themes: Social media habits (stalking, comparing, checking stories obsessively), texting anxiety (overthinking replies, being left on read, double texting fear), modern dating (ghosting, breadcrumbing, situationships), adulting struggles (imposter syndrome, quarter-life crisis, burnout), procrastination, self-sabotage, FOMO, doomscrolling, late-night overthinking, avoidance patterns, comfort zone behaviors, online shopping therapy.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy to understand)
* MUST be immediately relatable to Gen-Z/Millennials TODAY
* Specific modern behavior (not vague emotions)
* Makes readers go: "This is TOO accurate!"
* Can reference: apps, texting, social media, WFH, streaming, food delivery, online habits
* Honest and self-aware
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Adding things to your cart and never buying them because it feels like committing to a future you're not sure about."
- "Typing a whole paragraph, staring at it for five minutes, deleting it all, and just sending 'lol yeah.'"

Return only the moment.
""",

    "SHORT_CONVERSATION": f"""
Create a relatable conversation between two people.

{CONVERSATION_NAMES}

Themes: Modern relationships, situationships, friendship dynamics, family misunderstandings, late-night thoughts, miscommunication, realizations, bittersweet moments, growing up, emotional honesty, vulnerability, comfort, understanding.

Requirements:
* 4-7 exchanges MAXIMUM (keep it short)
* Each dialogue line must be VERY SHORT - maximum 5-6 words
* SIMPLE ENGLISH (easy words, how people actually talk)
* Natural, modern dialogue
* Must feel authentic, not scripted
* Emotional punch or quiet revelation
* Final line should hit differently
* NO religious, cultural, or gender stereotypes

CRITICAL FORMAT RULES:
* Each line MUST start with "Name: " followed by dialogue
* Each exchange on a NEW LINE
* Maximum 28 characters per line INCLUDING "Name: " prefix
* Keep dialogue EXTREMELY brief (5-6 words max)
* Simple responses like: "Yeah.", "Me too.", "I know.", "Why?", "When?"

Correct Format Example:
Mila: Are you awake?
Kai: Yeah. Can't sleep.
Mila: Me neither.
Kai: Thinking about what?
Mila: How everything changed.
Kai: I know what you mean.

Return only the conversation (no intro, strict line-by-line format).
""",

    "HE_SHE_RELATIONSHIP": """
Create a punchy, brutally honest observation about modern dating/relationships using he/she/they pronouns.

Themes: Mixed signals, effort imbalance, emotional unavailability, breadcrumbing, orbiting, benching, situationships, "just talking" phase, effort vs interest, actions vs words, attachment anxiety, post-breakup behavior, red flags, knowing your worth, settling vs waiting.

Requirements:
* 12-20 words MAXIMUM (short and punchy)
* SIMPLE ENGLISH (easy words)
* Uses "he" or "she" or "they" naturally
* Relatable to modern dating reality
* Brutally honest but not bitter/preachy
* Validating or eye-opening
* Screenshot-worthy
* Format: 1 sentence
* No emojis or hashtags

Examples (do NOT copy):
- "She texts back in 5 seconds or 5 hours, there's no in between and both mean something."
- "He'll say he's not ready for a relationship but somehow has energy for you at 2 AM."

Return only the observation.
""",

    "CHILDHOOD_VS_NOW": """
Create a nostalgic comparison between childhood and adult life that hits emotionally.

Format: "Childhood: [nostalgic thing] / Adulthood: [harsh reality]"

Themes: Lost innocence, responsibilities, burnout, comparison culture, financial stress, career pressure, relationships complexity, adulting struggles, nostalgia for simpler times, exhaustion, disillusionment, quarter-life crisis.

Requirements:
* Total 20-35 words (both parts combined)
* SIMPLE ENGLISH (easy to understand)
* Two-part structure: Childhood vs Adulthood
* Must be universally relatable to 18-34 year olds
* Honest about adult struggles
* Nostalgic but not overly sad
* Gender-neutral
* No emojis or hashtags

Examples (do NOT copy):
- "Childhood: Excited about growing up and having freedom / Adulthood: Realizing freedom means bills, burnout, and pretending you have it together."

Format: Keep "Childhood:" and "Adulthood:" labels

Return only the comparison.
""",

    "POP_CULTURE_LYRICS": """
Generate a reference to a popular song lyric, movie quote, or trending cultural moment that resonates.

Themes: Viral song lyrics (from trending songs), iconic movie lines, meme culture references, TV show quotes, trending audio, relatable pop culture moments, nostalgic references (90s/2000s), current hits.

Requirements:
* 10-25 words
* SIMPLE ENGLISH (easy to understand)
* Reference must be widely recognizable to 18-34 year olds
* Can be direct quote or creative adaptation
* Relatable context
* Gender-neutral when possible
* Should feel current or nostalgically familiar
* Format: 1 sentence or song lyric format
* No emojis or hashtags

Examples (do NOT copy):
- "Some days you're the main character. Other days you're just part of the soundtrack."
- "Not me thinking I'm the problem when really I'm the solution they couldn't handle."

Return only the pop culture reference.
""",

    "NATURE_UNIVERSE": """
Generate a perspective-shifting observation about nature, the universe, or cosmic scale.

Themes: Stars and galaxies, ocean depth, mountain majesty, seasons and cycles, cosmic perspective, human insignificance vs significance, natural patterns, universe's wisdom, planetary scale, astronomical wonder, nature as teacher, existential awe.

Requirements:
* 20-35 words
* SIMPLE ENGLISH (easy words, no complicated science terms)
* Awe-inspiring or perspective-shifting
* References nature or cosmos
* Makes human problems feel smaller or connects us to something bigger
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "The ocean doesn't try to hold every wave. It lets them come and go. You can too."
- "Mountains don't compete. Trees don't compare. Rivers don't rush. Nature just exists, and somehow that's enough."

Return only the cosmic observation.
""",

    "LIFE_WISDOM": """
Generate a philosophical observation or life lesson that offers perspective and wisdom.

Themes: Time and impermanence, human nature, what truly matters, lessons from experience, perspective on suffering, finding meaning, understanding people, acceptance of life's chaos, simple truths, philosophical insights, universal patterns.

Requirements:
* 20-35 words
* SIMPLE ENGLISH (no fancy philosophy words)
* Wise and reflective (not preachy)
* Timeless truth or observation
* Can reference nature, time, human behavior, or life patterns
* Philosophical but accessible
* Gender-neutral
* Not advice - just an observation
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "We spend our twenties collecting people and our thirties learning that a few deep roots matter more than a forest of shallow ones."
- "The same boiling water that softens the potato hardens the egg. It's not about the circumstance, it's what you're made of."

Return only the wisdom.
""",

    "DEEP_EMOTIONAL": """
Generate ONE completely original quote about a deeply human emotional experience.

Themes: heartbreak, lost love, missing someone who's still alive, emotional distance, silent goodbyes, growing apart, nostalgia, regret, loneliness, healing that never fully arrives, loving someone who became a stranger, grief without closure, outgrowing places that felt like home, friendships fading, watching loved ones age, fear of being forgotten, losing versions of yourself, dreams abandoned halfway, ordinary days that became precious, the ache of change, words left unsaid, endings that arrived unnoticed.

Requirements:
* 20-30 words
* SIMPLE ENGLISH (easy to understand, poetic but not fancy)
* Universally relatable
* Gender-neutral (NEVER use: he, she, him, her, boyfriend, girlfriend, husband, wife, mother, father, son, daughter, brother, sister)
* Deeply emotional but intimate, not dramatic
* Like a thought at 2 AM
* Fresh and surprising - avoid every cliché
* NO common metaphors: broken hearts, shattered pieces, storms, rain, oceans, waves, stars, sunsets, mirrors, scars, echoes, fading photographs, fire, ashes
* Use vivid emotional imagery around ordinary moments
* No advice, lesson, or forced optimism
* Format: 2-3 short paragraphs
* No emojis, hashtags, quotation marks

Return only the quote.
""",

    "ONE_LINER": """
Generate ONE powerful single-sentence quote about love, heartbreak, life, or growth.

Requirements:
* Exactly ONE sentence
* 10-20 words maximum
* SIMPLE ENGLISH (easy words)
* Instantly quotable and shareable
* Emotionally striking
* Can be: romantic, painful, philosophical, or bittersweet
* Gender-neutral
* Fresh take on universal feelings
* Should make people want to tag someone or save it
* No emojis or hashtags

Examples (do NOT copy):
- "Some goodbyes happen in silence, and you spend years replaying the last normal conversation."
- "You can miss someone and still know leaving was right."

Return only the one-liner.
""",

    "THINGS_NOBODY_TALKS_ABOUT": """
Reveal an unspoken truth or hidden experience that everyone goes through but rarely admits.

Themes: Mental health struggles nobody mentions, adulting secrets, relationship truths, social anxiety moments, imposter syndrome, comparison culture pain, hidden loneliness, fake social media life vs reality, financial stress shame, career doubts, friendship changes, family pressure, burnout signs.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy to understand)
* Starts with "Nobody talks about..." or implies it
* Addresses something people hide or don't discuss openly
* Validating and honest (not preachy)
* Makes readers feel less alone
* Can be vulnerable but not depressing
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Nobody talks about how exhausting it is to constantly pretend you're doing fine when you're barely holding it together."
- "Nobody talks about the loneliness of having people around you but still feeling completely misunderstood."

Return only the statement.
""",

    "UNPOPULAR_OPINION": """
Share a slightly controversial but deeply relatable opinion that challenges common narratives.

Themes: Hustle culture critique, relationship standards, social media reality, self-care truth, productivity pressure, comparison culture, "living your best life" myth, toxic positivity, career expectations, friendship quality over quantity, boundaries, saying no, rest as necessity not luxury.

Requirements:
* 15-25 words
* SIMPLE ENGLISH (easy words)
* Can start with "Unpopular opinion:" or state it directly
* Challenges mainstream narratives but in a relatable way
* Not actually controversial - just honest
* Should make people nod and say "FACTS"
* Validating, not preachy
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Unpopular opinion: You don't have to be constantly productive to deserve rest. Existing is exhausting enough."
- "Unpopular opinion: It's okay to outgrow friendships. Not every relationship is meant to last forever."

Return only the opinion.
""",

    "WHOLESOME_JOY": """
Capture a small, pure moment of happiness, comfort, connection, or unexpected joy.

Requirements:
* 15-25 words
* SIMPLE ENGLISH (easy words)
* Describes a specific, relatable moment of lightness
* Not overly cheerful or fake - just quietly nice
* Can be: comforting, warm, peaceful, or gently funny
* Universal across cultures
* Gender-neutral
* Makes readers smile softly, not cringe
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "When someone remembers the small thing you mentioned once, and brings it up weeks later."
- "The relief of laughing so hard with someone that you forget what you were worried about."

Return only the moment.
""",

    "TRAVEL_WANDERLUST": """
Generate an inspiring message about travel, adventure, exploration, or wanderlust.

Themes: Exploring the world, adventure calling, escaping routine, finding yourself through travel, collecting experiences, cultural discovery, road trips, new horizons, unknown paths, wanderlust spirit, nomadic life, freedom of movement.

Requirements:
* 15-30 words
* SIMPLE ENGLISH (easy words)
* Adventurous and inspiring
* Travel/exploration focused
* Can be about physical travel or metaphorical journeys
* Universal (not everyone can afford to travel - be inclusive)
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Not all who wander are lost. Some are just searching for a place that feels more like home than home does."
- "Sometimes you need to get lost in new streets to find yourself again."

Return only the wanderlust message.
""",
}


def get_prompt_for_current_time():
    """
    Get the appropriate prompt based on current time
    Returns only the relevant prompt to save Gemini tokens
    """
    content_info = get_content_type_for_time()
    content_type = content_info['type']
    
    print(f"\n📝 Generating: {content_info['name']}")
    print(f"💡 Context: {content_info['reason']}")
    
    # Get the specific prompt
    if content_type in ALL_PROMPTS:
        prompt = f"{BASE_INSTRUCTION}\n\n{ALL_PROMPTS[content_type]}"
    else:
        # Fallback
        print(f"⚠️ Type '{content_type}' not found, using motivational fallback")
        prompt = f"{BASE_INSTRUCTION}\n\n{ALL_PROMPTS['MOTIVATIONAL_INSPIRING']}"
    
    print(f"✅ Prompt prepared ({len(prompt)} characters)")
    return prompt


if __name__ == "__main__":
    # Test
    prompt = get_prompt_for_current_time()
    print("\n" + "="*60)
    print("PROMPT TO SEND TO GEMINI:")
    print("="*60)
    print(prompt[:500] + "...")

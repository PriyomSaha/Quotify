"""
PromptSelector.py - Efficiently select and return only the needed prompt
Saves Gemini API tokens by sending only relevant content type
"""

from content_schedule import get_content_type_for_time
import random


# Compact angle bank: Python selects ONE angle so we don't send a large
# topic list to Gemini on every request.
HUMAN_TRUTH_ANGLES = [
    "people slowly growing apart",
    "missing who someone used to be",
    "friendships fading without a fight",
    "outgrowing an old version of yourself",
    "ordinary moments becoming memories",
    "being close to someone but feeling distant",
    "remembering a time rather than a person",
    "relationships becoming one-sided",
    "childhood friendships changing with adulthood",
    "things ending without a clear goodbye",
    "having many contacts but few real connections",
    "realizing you cannot return to how things were",
    "caring about someone who no longer feels familiar",
    "noticing someone has changed without knowing when",
    "wanting to say something but choosing silence",
]

# Base instruction for all types
BASE_INSTRUCTION = """You are a content creator for "Aesthetic Vibes" - a page for lost souls finding their way home through words.

Your audience: 90% South Asian (India, Bangladesh, Nepal, Pakistan), 18-34 years old, mostly women, who want content that feels personal, relatable, touching, and worth sharing.

IMPORTANT - SIMPLE WORDS ONLY:
* Write every quote like you are telling it to a friend over chai. Use simple, everyday words.
* Avoid long, fancy, heavy, rare, or complicated words.
* Every reader should understand the feeling in one read.

RELATABILITY:
* Prefer real human behavior, small everyday moments, and honest observations over abstract poetry.
* Be specific rather than generic. Make readers think "that's exactly me."
* When it suits the theme, use one small everyday detail naturally; never force it.
* Add a subtle twist, quiet irony, fresh realization, or emotional truth.
* Make the feeling felt instead of simply naming the emotion.
* End with something natural that stays in the reader's mind and feels worth saving or sharing.
* Vary the delivery so the feed does not feel repetitive or formulaic.
* Not every quote needs to be sad, deep, poetic, or motivational.
* The goal is recognition and genuine emotion, not trying to sound deep or viral.

ORIGINALITY:
* Create a fresh angle on familiar human experiences.
* Avoid common Instagram quote clichés, predictable phrases, recycled ideas, and overused metaphors.
* Do not make a quote sound like something thousands of quote pages have already posted.
* Prefer an original observation over a generic life lesson.

Before returning, read the content back. Replace any heavy word with a simpler everyday word and remove anything that feels forced, cliché, or generic.

Generate content for the specified type ONLY. Return ONLY the content - no labels, explanations, or commentary."""

# ALL PROMPT TEMPLATES
ALL_PROMPTS = {

    "HUMAN_TRUTH": """
Write ONE original quote about a quiet truth people commonly experience.

Start with an ordinary human observation.
Reveal what that behavior really means emotionally.
End with a subtle, memorable realization.

Make it feel personally experienced but universally relatable.

Use simple everyday English.
Deep but natural.
Emotional but controlled.
Sound like a private realization, not a motivational quote.

Avoid clichés, advice, therapy language, dramatic poetry,
forced metaphors, and generic statements.

12–32 words.
No quotation marks, hashtags, or emojis.
Return ONLY the quote.
""",
    
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

    "FRIENDSHIP_BONDS": """
Generate a heartfelt message about friendship, loyalty, chosen family, or deep platonic bonds.

Themes: True friends who stay, chosen family, loyalty through hard times, friends who become family, unconditional support, laughing until you cry, inside jokes, friends who get you, being yourself around them, distance doesn't matter, quality over quantity, ride-or-die energy, friendship appreciation.

Requirements:
* 18-28 words
* SIMPLE ENGLISH (easy words)
* Celebrates platonic love and friendship
* Warm and appreciative tone
* NOT romantic - purely friendship focused
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Real friends don't ask if you need help. They just show up with food, bad jokes, and zero judgment."
- "Find friends who feel like home, not just people who know your address."

Return only the friendship message.
""",

    "SELF_LOVE_BOUNDARIES": """
Generate a powerful message about self-worth, setting boundaries, choosing yourself, or breaking toxic patterns.

Themes: Knowing your worth, setting boundaries without guilt, choosing yourself first, walking away from toxicity, unlearning people-pleasing, self-respect, protecting your peace, saying no, healing relationship with yourself, breaking generational patterns, self-validation, refusing to shrink yourself.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy words)
* Empowering and validating
* About self-worth or boundaries
* Not selfish - just healthy
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "You're allowed to outgrow people who refuse to water your growth. Boundaries aren't walls, they're bridges to better."
- "Stop shrinking yourself to fit into rooms that were never built for your expansion."

Return only the self-love message.
""",

    "MENTAL_HEALTH_REAL": """
Create an honest, validating message about mental health, anxiety, depression, burnout, or emotional exhaustion.

Themes: It's okay not to be okay, invisible struggles, high-functioning anxiety, burnout recovery, healing isn't linear, mental health matters, rest without guilt, asking for help, therapy normalization, breaking the stigma, emotional exhaustion, surviving vs living.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy words)
* Validating and compassionate (NOT toxic positivity)
* Honest about struggles
* Makes people feel seen and less alone
* Not preachy or advice-heavy
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Sometimes self-care is just making it through the day without falling apart. That's enough. You're enough."
- "Your mental health is not a trend or aesthetic. It's real, it's valid, and it deserves attention."

Return only the mental health message.
""",

    "DAILY_STRUGGLE_HUMOR": """
Create humor about specific daily struggles - work, family, money, responsibilities, or modern life chaos.

Themes: Work stress and boss dynamics, family expectations and comparisons, salary never enough, bills arriving on time (unlike motivation), student life chaos, commute nightmares, household chores piling up, adulting admin tasks, phone storage full, low battery anxiety, passwords forgotten, online meeting disasters.

Requirements:
* 15-25 words
* SIMPLE ENGLISH (easy words)
* Specific situation humor (not vague funny feeling)
* Relatable to working adults/students
* Self-aware and witty
* Can reference: jobs, family, money, chores, technology
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "My salary arrives and leaves faster than guests who said they'd stay for just 5 minutes."
- "Parents: 'Don't believe everything on internet.' Also parents: forwards every WhatsApp message."

Return only the struggle humor.
""",

    "DREAMS_AMBITIONS": """
Generate an inspiring message about chasing dreams, building your vision, or following your passion.

Themes: Side hustle energy, passion projects, creative pursuits, building your empire, manifesting dreams, taking leaps of faith, betting on yourself, creating your future, vision board life, 5-year plan, grinding for your dreams, turning hobbies into income, entrepreneurial spirit.

Requirements:
* 18-28 words
* SIMPLE ENGLISH (easy words)
* Inspiring and ambitious
* About personal dreams/goals (not generic success)
* Hopeful but realistic
* Encourages action
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Your 9-to-5 pays your bills. Your 5-to-9 builds your dreams. Don't abandon the vision just because it's tired."
- "Someone once told me my dreams were too big. I outgrew them and their opinions."

Return only the dream message.
""",

    "FOOD_COMFORT": """
Create a warm, relatable message about food, comfort eating, home cooking, or food memories.

Themes: Comfort food therapy, mom's cooking nostalgia, midnight snacks, street food memories, cooking fails, food delivery addiction, emotional connection to food, sharing meals with loved ones, kitchen experiments, food = love language, taste of home.

Requirements:
* 15-25 words
* SIMPLE ENGLISH (easy words)
* Warm and relatable
* Food-related (cooking, eating, memories)
* Can be nostalgic, funny, or comforting
* Culturally inclusive (not specific to one cuisine)
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Some comfort can't be explained by therapists. It lives in the smell of home-cooked food and familiar kitchens."
- "Midnight Maggi hits different when you're fixing your life one noodle at a time."

Return only the food message.
""",

    "MUSIC_ART_SOUL": """
Generate a message about how music, art, or creativity heals, inspires, or connects us.

Themes: Songs that heal, music as therapy, old songs nostalgia, artists who saved you, lyrics that understand, art as expression, creativity as escape, finding yourself in melodies, music memories, soundtracks of life, emotional connection to art.

Requirements:
* 18-28 words
* SIMPLE ENGLISH (easy words)
* Emotional connection to music/art
* Universal (not specific artist/song)
* Can be nostalgic or healing
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Some songs don't just play in your ears. They rewind your memory to moments you thought you'd forgotten."
- "Music doesn't fix broken hearts, but it sits with you in the dark until sunrise comes."

Return only the music/art message.
""",

    "PHILOSOPHICAL_LIGHT": """
Share a light philosophical observation about life, destiny, karma, timing, or universe's patterns.

Themes: Everything happens for a reason (but gentle), karma exists, timing is everything, universe has plans, destiny and free will, cosmic justice, life's patterns, circles closing, wrong paths leading to right places, coincidences that aren't, lessons disguised as losses.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy words)
* Philosophical but accessible
* Spiritual/mystical vibe (NOT religious)
* Comforting perspective
* Not preachy
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Sometimes wrong trains take you to right destinations. Trust the detours, they're part of the map."
- "The universe removes people from your life when their part in your story is complete. Let them go."

Return only the philosophical message.
""",

    "SOCIAL_COMMENTARY": """
Create gentle social commentary about modern culture, society, or behavioral trends.

Themes: Social media fakeness, hustle culture toxicity, comparison culture, modern dating chaos, performative activism, influencer culture, validation addiction, digital age loneliness, screen time vs real time, online personas vs reality, productivity obsession, cancel culture, virtue signaling.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy words)
* Observational, not preachy
* Critiques behavior/culture gently
* Relatable and thought-provoking
* Not political or divisive
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "We document moments to prove we're living them, then forget to actually live them while documenting."
- "Everyone's selling a dream life online but nobody's buying the truth that they're just as lost."

Return only the commentary.
""",

    "OVERTHINKING_ANXIETY": """
Capture the experience of overthinking, anxiety spirals, or the exhausting mental loops we get stuck in.

Themes: Overthinking everything, analyzing texts for hours, worst-case scenarios, anxiety spirals, catastrophizing, replaying conversations, creating problems that don't exist, paralysis by analysis, fear of the unknown, waiting for bad news, assuming the worst, mental exhaustion from thoughts.

Requirements:
* 18-28 words
* SIMPLE ENGLISH (easy words)
* Captures overthinking experience vividly
* Validating (makes overthinkers feel seen)
* Honest but not scary
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Overthinking is when you create six different arguments with someone who probably forgot the conversation five minutes ago."
- "Anxiety is your mind writing horror stories about tomorrow using yesterday's worst moments as reference."

Return only the overthinking message.
""",

    "LIFE_LESSONS_SUGGESTIONS": """
Share a practical life lesson, piece of advice, or wisdom gained from experience.

Themes: Things I wish I knew earlier, lessons from mistakes, advice to younger self, relationship lessons, career wisdom, money management, friendship advice, communication skills, boundary lessons, self-awareness tips, choosing battles wisely, understanding people.

Requirements:
* 20-35 words
* SIMPLE ENGLISH (easy words)
* Practical wisdom or life lesson
* From personal experience perspective
* Helpful without being preachy
* Can start with: "I learned...", "Life taught me...", "I wish I knew..."
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "I learned that people show you who they are consistently. Believe patterns, not apologies. Words are cheap, actions build trust."
- "Life taught me that protecting your peace isn't selfish. You can't pour from an empty cup."

Return only the life lesson.
""",

    "GROWTH_HEALING": """
Create a message about personal growth, healing journey, or transformation.

Themes: Healing isn't linear, growing pains, becoming unrecognizable to old self, outgrowing old versions, shedding old skin, learning to let go, finding yourself after loss, rebuilding from scratch, transformation through pain, evolution not perfection, slow progress still progress.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy words)
* About growth or healing process
* Honest about difficulty
* Hopeful but realistic
* Validates the journey
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Healing doesn't mean the damage never existed. It means it no longer controls your life."
- "You're not the same person you were last year. Growth looks messy before it looks beautiful."

Return only the growth message.
""",

    "LATE_NIGHT_THOUGHTS": """
Capture those deep, vulnerable thoughts that hit at 2 AM when you're alone with your mind.

Themes: Midnight existential crisis, late-night realizations, 2 AM emotions, sleepless overthinking, vulnerable reflections, questions without answers, loneliness at night, processing emotions, confronting truths, rawness of night thoughts, unfiltered feelings.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy words)
* Feels like a 2 AM thought
* Raw and vulnerable
* Deeply relatable
* Honest without being depressing
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "It's 2 AM and I'm wondering if I'm building my life or just surviving it with better distractions."
- "Late-night thoughts hit different when you realize you're not healing, just getting better at hiding."

Return only the late-night thought.
""",

    "SMALL_VICTORIES": """
Celebrate small wins, everyday achievements, or tiny progress that deserves recognition.

Themes: Getting out of bed on hard days, completing small tasks, saying no without guilt, asking for help, eating when depressed, showering during burnout, one good day after many bad ones, small steps forward, progress not perfection, gentle wins.

Requirements:
* 15-25 words
* SIMPLE ENGLISH (easy words)
* Celebrates small, relatable achievements
* Validating and gentle
* Makes people feel proud of small things
* Not patronizing
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Getting out of bed on a hard day isn't lazy. It's choosing yourself when everything feels heavy."
- "You did one small thing today that past you would be proud of. That counts."

Return only the small victory message.
""",

    "FORGIVENESS_LETTING_GO": """
Create a message about forgiveness, letting go, moving on, or releasing what no longer serves you.

Themes: Forgiving yourself, releasing grudges, letting people go with love, closure you create yourself, moving forward without answers, peace over being right, releasing expectations, accepting endings, forgiving without forgetting, choosing peace over revenge.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy words)
* About forgiveness or letting go
* Empowering, not weak
* Validates difficulty of process
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Forgiveness doesn't mean what they did was okay. It means you refuse to carry their mistakes into your future."
- "Sometimes closure is accepting you'll never get the apology you deserved and choosing peace anyway."

Return only the forgiveness message.
""",

    "TIME_PERSPECTIVE": """
Share an observation about time, aging, change, or how quickly life moves.

Themes: Time flies, years blending together, age sneaking up, yesterday feels like last week, moments that define decades, time's relativity, looking back in disbelief, future arriving too fast, nostalgia for recent past, temporal dissonance, fleeting moments.

Requirements:
* 18-30 words
* SIMPLE ENGLISH (easy words)
* About time's passage or perspective
* Relatable across ages
* Reflective but not depressing
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "Crazy how you can be 18 thinking you have forever, blink twice, and suddenly you're 28 wondering where time went."
- "Time is weird. Days feel long but years disappear. Moments feel small but memories last forever."

Return only the time perspective.
""",

    "TRUTH_BOMBS": """
Drop a harsh truth or reality check that people need to hear (delivered with care).

Themes: Uncomfortable truths, reality checks, things people avoid hearing, difficult acceptance, wake-up calls, honest observations about life/love/work, illusions we hold, self-deception we practice, avoidance patterns, truths that hurt but help.

Requirements:
* 15-25 words
* SIMPLE ENGLISH (easy words)
* Harsh truth delivered kindly
* Reality check without cruelty
* Makes people uncomfortable but in helpful way
* Not mean-spirited
* Gender-neutral
* Format: 1-2 sentences
* No emojis or hashtags

Examples (do NOT copy):
- "If they wanted to, they would. Stop creating excuses for people who barely think about you."
- "You can't heal in the same environment that made you sick. Sometimes leaving is self-care."

Return only the truth bomb.
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


LAST_SELECTED_CONTENT_INFO = None


def get_prompt_for_current_time(record_history=True):
    """
    Get the appropriate prompt based on current time.
    Returns only the relevant prompt to save Gemini tokens.
    """
    global LAST_SELECTED_CONTENT_INFO
    content_info = get_content_type_for_time(record_history=record_history)
    LAST_SELECTED_CONTENT_INFO = content_info
    content_type = content_info['type']

    # Select one angle in Python so the full angle bank is never sent to Gemini.
    human_truth_angle = None
    if content_type == "HUMAN_TRUTH":
        human_truth_angle = random.choice(HUMAN_TRUTH_ANGLES)
    
    print(f"\n📝 Generating: {content_info['name']}")
    print(f"💡 Context: {content_info['reason']}")
    
    # Get the specific prompt
    if content_type in ALL_PROMPTS:
        prompt = f"{BASE_INSTRUCTION}\n\n{ALL_PROMPTS[content_type]}"

        if human_truth_angle:
            prompt += f"\nFocus on this human experience: {human_truth_angle}"
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

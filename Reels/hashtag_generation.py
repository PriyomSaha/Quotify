import random
from typing import Optional, Dict, Any

from event_detector import build_event_caption_prefix, get_event_hashtags

# Always included
FIXED_HASHTAGS = [
    "#LifeQuotes",
    "#LifeLessons",
    "#Reels",
]

# Random pool
HASHTAG_POOL = [
    "#Quotes",
    "#Quote",
    "#QuoteOfTheDay",
    "#DailyQuote",
    "#DailyQuotes",
    "#QuoteLife",
    "#InspirationalQuotes",
    "#MotivationalQuotes",
    "#PositiveQuotes",
    "#WisdomQuotes",
    "#PowerfulQuotes",
    "#MeaningfulQuotes",
    "#DeepQuotes",
    "#FamousQuotes",
    "#QuoteLover",
    "#Words",
    "#WordsOfWisdom",
    "#WiseWords",
    "#Thoughts",
    "#DeepThoughts",
    "#DailyWisdom",
    "#Life",
    "#LifeAdvice",
    "#LifeJourney",
    "#LifeMotivation",
    "#LifeInspiration",
    "#LifeTips",
    "#Advice",
    "#GoodAdvice",
    "#Motivation",
    "#Inspiration",
    "#Success",
    "#SuccessMindset",
    "#Growth",
    "#GrowthMindset",
    "#SelfGrowth",
    "#PersonalGrowth",
    "#SelfImprovement",
    "#SelfDevelopment",
    "#BetterYourself",
    "#Mindset",
    "#PositiveMindset",
    "#PositiveThinking",
    "#Discipline",
    "#Habits",
    "#Focus",
    "#Consistency",
    "#Family",
    "#FamilyFirst",
    "#FamilyLove",
    "#FamilyTime",
    "#FamilyGoals",
    "#Parents",
    "#Parenting",
    "#ParentingTips",
    "#Relationship",
    "#Relationships",
    "#Love",
    "#Respect",
    "#Trust",
    "#Kindness",
    "#Gratitude",
    "#Togetherness",
    "#Home",
    "#Marriage",
    "#HealthyRelationships",
    "#MentalHealth",
    "#InnerPeace",
    "#Peace",
    "#Healing",
    "#HealingJourney",
    "#SelfCare",
    "#SelfLove",
    "#EmotionalHealing",
    "#Mindfulness",
    "#CalmMind",
    "#Hope",
    "#Happiness",
    "#Joy",
    "#Positivity",
    "#BeKind",
    "#DailyMotivation",
    "#NeverGiveUp",
    "#KeepGoing",
    "#DreamBig",
    "#BelieveInYourself",
    "#HardWork",
    "#SuccessQuotes",
    "#GoalSetter",
    "#WorkHard",
    "#MindsetMatters",
    "#StayStrong",
    "#BeBetter",
    "#WinTheDay",
    "#Inspirational",
    "#Inspire",
    "#InspireDaily",
    "#InspirationalWords",
    "#DailyInspiration",
    "#Encouragement",
    "#Faith",
    "#Believe",
    "#Purpose",
    "#Vision",
    "#Deep",
    "#RealTalk",
    "#Truth",
    "#Reality",
    "#TruthOfLife",
    "#Emotions",
    "#Feelings",
    "#Heart",
    "#Soul",
    "#InnerStrength",
    "#Reflection",
    "#SelfReflection",
    "#LessonsLearned",
    "#WakeUpCall",
    "#InstagramReels",
    "#ReelsInstagram",
    "#Reel",
    "#ReelVideo",
    "#ReelCreator",
    "#ReelLife",
    "#Explore",
    "#ExplorePage",
    "#ExploreMore",
    "#Viral",
    "#Trending",
    "#TrendingReels",
    "#ContentCreator",
    "#Creators",
    "#DailyContent",
    "#ShortVideo",
    "#VideoOfTheDay",
    "#Productivity",
    "#Goals",
    "#GoalSetting",
    "#Leadership",
    "#BusinessMindset",
    "#Entrepreneur",
    "#Winning",
    "#Ambition",
    "#DisciplineEqualsFreedom",
    "#LearnEveryDay",
    "#KeepLearning",
    "#DailyReminder",
    "#DailyThought",
    "#Reminder",
    "#SimpleLiving",
    "#HealthyMind",
    "#PositiveVibes",
    "#GoodVibes",
    "#Humble",
    "#Wisdom",
    "#Character",
    "#RespectEveryone",
    "#Humanity",
    "#KindnessMatters",
    "#LiveBetter",
    "#LiveInspired",
    "#BeYourBest",
    "#LifeIsBeautiful",
    "#ChooseKindness",
    "#StayPositive",
    "#BeHappy",
]


def generate_hashtags(min_count=20, max_count=23, event: Optional[Dict[str, Any]] = None):
    """
    Returns a string of 20-23 hashtags.
    Always includes:
        #LifeQuotes
        #LifeLessons
        #Reels
    """

    event_tags = get_event_hashtags(event)
    fixed_tags = list(dict.fromkeys(FIXED_HASHTAGS + event_tags))

    if min_count < len(fixed_tags):
        min_count = len(fixed_tags)

    if max_count < min_count:
        max_count = min_count

    total = random.randint(min_count, max_count)
    available_pool = [tag for tag in HASHTAG_POOL if tag not in fixed_tags]
    random_count = min(total - len(fixed_tags), len(available_pool))

    random_tags = random.sample(
        available_pool,
        random_count
    )

    hashtags = fixed_tags + random_tags
    random.shuffle(hashtags)

    return " ".join(hashtags)


def build_reel_caption(
    title: str = "",
    fallback_text: str = "",
    max_title_chars: int = 300,
    event: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a Meta-safe reel caption with hashtags clearly appended.

    Keep only two line breaks between title and hashtags. Too many blank lines
    can make logs/social previews look like only the title was sent.
    """
    clean_title = (title or fallback_text or "Aesthetic Vibes").strip()
    clean_title = " ".join(clean_title.split())[:max_title_chars].strip()

    event_prefix = build_event_caption_prefix(event)
    if event_prefix and event_prefix.lower() not in clean_title.lower():
        clean_title = f"{event_prefix}: {clean_title}"

    hashtags = generate_hashtags(event=event).strip()

    return f"{clean_title}\n\n{hashtags}"


if __name__ == "__main__":
    print(generate_hashtags())
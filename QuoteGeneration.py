from google import genai
import os
from dotenv import load_dotenv
from PromptSelector import get_prompt_for_current_time
from event_detector import CONTENT_QUOTE, build_quote_event_instruction, get_today_event

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def generate_quote(record_history=True):
    """
    Generate content based on current time.
    Uses time-based prompt selection to save tokens and ensure variety.
    """
    # Get the appropriate prompt for current time
    prompt = get_prompt_for_current_time(record_history=record_history)

    # Optional enhancement: if today is a configured special event,
    # add event context without changing the default random logic.
    event = get_today_event(content_type=CONTENT_QUOTE)
    if event:
        prompt += build_quote_event_instruction(event)
    
    # Generate content using Gemini
    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )

    return interaction.output_text
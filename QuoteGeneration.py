from google import genai
import os
from dotenv import load_dotenv
from PromptSelector import get_prompt_for_current_time

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
    
    # Generate content using Gemini
    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )
    
    return interaction.output_text
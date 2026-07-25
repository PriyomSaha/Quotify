from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

with open("prompt.txt", "r", encoding="utf-8") as f:
    prompt = f.read()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input=prompt
)

def generate_quote():
    return(interaction.output_text)
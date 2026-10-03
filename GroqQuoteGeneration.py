import os

from dotenv import load_dotenv


load_dotenv()


def generate_text_with_groq(prompt):
    """Generate text with Groq's OpenAI-compatible Responses API."""
    from openai import OpenAI

    api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Groq fallback requires GROQ_API_KEY (or the legacy GROK_API_KEY)."
        )

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    response = client.responses.create(
        input=prompt,
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    )
    output_text = (response.output_text or "").strip()
    if not output_text:
        raise RuntimeError("Groq returned empty text.")

    return output_text
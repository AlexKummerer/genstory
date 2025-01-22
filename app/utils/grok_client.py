import asyncio
import json
import httpx
from typing import Dict
from dotenv import load_dotenv
import os

load_dotenv()



# Environment variables for API key and endpoint
GROK_API_URL = "https://api.x.ai/v1/chat/completions"  # Replace with the real URL
GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_MODEL = "grok-beta"


async def generate_character_with_grok(
    description: str, name: str | None = None
) -> Dict:
    """
    Generate character details using Grok API.

    Args:
        description (str): The character description.
        name (str | None): Optional existing name for the character.

    Returns:
        Dict: Generated character data including traits, context, summary, and optionally a name.
    """
    if not GROK_API_KEY:
        raise ValueError(
            "Grok API key not found. Please set the GROK_API_KEY environment variable."
        )

    prompt = f"""
    You are a creative AI assistant that is excellent in story telling and created characters. Based on the following description, generate :
    - A name (if not provided): A fitting name for the character.
    - Traits (in JSON format): A dictionary describing personality traits (e.g., bravery, intelligence).
    - Story context: A short paragraph providing context for this character.
    - Summary: A one-sentence summary of the character.
    in response to the given description.
    
    Description: "{description}"
    {f'Name: "{name}"' if name else "Name: None"}
    
    IMPORTANT: 
    1. Optimize the description for clarity and creativity before proceeding.
    2. Regardless of the input language, all output MUST be in English.
    3. Respond ONLY with valid JSON formatted like this:
    {{
        "name": "Generated Name Here or given name",
        "description": "given description",
        "optimized_description": "The improved description here.",
        "generated_traits": {{"brave": true, "intelligent": false}},
        "story_context": "A story context here.",
        "generated_summary": "A summary here."
    }}
    """

    payload = {
        "model": GROK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }

    # Retry logic with timeout handling
    async def post_with_retry(url, headers, payload, retries=3, delay=5):
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()  # Raise exception for HTTP errors
                    return response
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(delay)  # Wait before retrying
                    continue
                raise e

    response = await post_with_retry(GROK_API_URL, headers, payload)

    try:
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
        if content.startswith("```json"):
            content = content.strip("```json").strip("```")
        character_data = json.loads(content)  # Convert string response to dict
        if not all(
            key in character_data
            for key in [
                "name",
                "description",
                "optimized_description",
                "generated_traits",
                "story_context",
                "generated_summary",
            ]
        ):
            raise ValueError("Invalid response format from Grok API.")
        return character_data
    except Exception as e:
        raise ValueError(f"Error parsing Grok API response: {str(e)}")

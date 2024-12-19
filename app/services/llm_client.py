import openai
from app.core.config import settings
from app.schemas.traits import Trait


class LLMClient:
    """Client for interacting with OpenAI's language model APIs."""

    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    async def generate_character_traits(self, description: str):
        """Generate character traits based on a description."""
        prompt = (
            f"Based on the following description, generate a list of character traits: \n"
            f"Description: {description}"
        )
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=200,
                temperature=0.7,
            )
            traits_text = response.choices[0].text.strip()
            traits = [
                Trait(name=trait.split(":")[0], value=trait.split(":")[1])
                for trait in traits_text.split("\n")
                if ":" in trait
            ]
            return traits
        except Exception as e:
            raise RuntimeError(f"Failed to generate character traits: {str(e)}")

    async def refine_story_context(self, context: str):
        """Refine a story context using the LLM."""
        prompt = (
            f"Refine the following story context for a more engaging and vivid narrative:\n"
            f"Context: {context}"
        )
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=200,
                temperature=0.7,
            )
            return response.choices[0].text.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to refine story context: {str(e)}")

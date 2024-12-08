import json
import os
from typing import Any, Coroutine

from groq import AsyncGroq, Groq
from pydantic import BaseModel

from app.db.db import Character


class CharacterUpdateInput(BaseModel):
    description: str | None = None
    name: str | None = None
    generated_traits: dict | None = None
    story_context: str | None = None

    def __repr__(self):
        return f"{self.description} {self.name} {self.generated_traits} {self.story_context}"


async def generate_character_with_groq(character_data: Character) -> Any:
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""
You are a creative AI assistant skilled in storytelling and character creation. Please refine and enhance the provided elements, and return optimzed details:

- **Name**: Generate a fitting name for the character.
- **Description**:provide an optimized version that adds more detail and context.
- **Traits**: provide an updated JSON-formatted dictionary with enhanced descriptions for these personality traits:
  - **Curious**: Make the description more specific, showing how this trait influences the character's actions and decisions.
  - **Brave**: Amplify the trait to highlight its impact on pivotal story developments.
  - **Sympathetic**: Enrich this trait to deepen the character's emotional connection with the audience.
  - **Cunning**: Expand on this trait to illustrate more complex strategic thinking or problem-solving.
  - **Resolute**: Strengthen this trait to emphasize the character's commitment and perseverance.
- **Story Context**:  provide a refined version that better sets the scene for the character’s role.

Given Data:
- Description: "{character_data.character_description}"
- Name: "{character_data.character_name}"
- Traits: "{character_data.character_traits}"
- Story Context: "{character_data.character_story_context}"

**Important Guidelines**:
1. Enhancements should increase clarity, depth, and creativity.
2. All responses must be in English, regardless of the input language.
3. Respond with a JSON object formatted as follows:

```json
{{
  "optimized_name": "Enhanced or generated name",
  "optimized_description": "Enhanced description with vivid details",
  "optimized_traits": {{
    "curious": "Updated description emphasizing exploration and its impact on the plot.",
    "brave": "Enhanced description focusing on how bravery shapes key moments.",
    "sympathetic": "Deepened description of empathy that connects with readers.",
    "cunning": "Expanded narrative on cunning, showing complex tactical acumen.",
    "resolute": "Strengthened portrayal of determination and its role in overcoming challenges."
  }},
  "optimized_story_context": "Refined narrative context aligning with the optimized traits and description",
}}
"""
    try:
        response = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative storyteller, that is excellent in story telling and created characters.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={
                "type": "json_object"
            },  # This is an example; adjust based on actual API requirements
            model="llama-3.1-70b-versatile",
        )
        print(response)

        if response.choices:
            choice = response.choices[0]
            message_content = choice.message.content
            chat_id = response.id  # Fetch the chat completion ID from the response

            # Parsing the JSON string within the message content
            try:
                character_data = json.loads(message_content)
                print("Character data parsed successfully:", character_data)
                return character_data, chat_id  # Return both character data and chat ID
            except json.JSONDecodeError:
                print("Failed to decode character data:", message_content)
                return None, chat_id  # Return None for character data and the chat ID
        else:
            print("No choices found in response.")
            return (
                None,
                "No ID found",
            )  # Return None for character data and indicate no ID found

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, "No ID found"


async def update_character_with_groq(character_data: CharacterUpdateInput):
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""
You are a creative AI assistant skilled in storytelling and character creation. Based on the provided character data, please **update** the following elements to enhance the character's development:

- **Traits**: Provide an updated JSON-formatted dictionary describing these personality traits:
  - **Curious**: Enhance the description to emphasize the character's curiosity in a way that drives the story forward.
  - **Brave**: Update to reflect how the character's bravery impacts pivotal story developments.
  - **Sympathetic**: Modify to deepen the character's connection with the audience.
  - **Cunning**: Refine to illustrate the character's skill in achieving goals through clever means, adding complexity to the plot.
  - **Resolute**: Adjust to highlight the character's unwavering determination in pursuing objectives.

- **Story Context**: Offer an updated paragraph that enriches the scene for this character's role in the story.

- **Summary**: Provide an updated concise one-sentence summary of the character reflecting any new developments or insights.

Given Data:
- Description: "{character_data.description}"
- Name: "{character_data.name}"
- Traits: "{character_data.generated_traits}"
- Story Context: "{character_data.story_context}"

**Important Guidelines**:
1. Enhance descriptions for maximum clarity and creativity.
2. All responses must be in English, regardless of the input language.
3. Respond with a JSON object formatted as follows:

```json
{{
  "optimized_name": "Enhanced name for clarity and creativity",
  "optimized_description": "Enhanced description for clarity and context",
  "generated_traits": {{
    "curious": "Description of curiosity trait",
    "brave": "Description of bravery trait",
    "sympathetic": "Description of sympathy trait",
    "cunning": "Description of cunning trait",
    "resolute": "Description of resoluteness trait"
  }},
      
  "generated_story_context": "Narrative context for the character's role in the story",
  }}
"""
    try:
        response = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative storyteller, that is excellent in story telling and created characters.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={
                "type": "json_object"
            },  # This is an example; adjust based on actual API requirements
            model="llama-3.1-70b-versatile",
        )
        print(response)

        if response.choices:
            choice = response.choices[0]
            message_content = choice.message.content
            # Fetch the chat completion ID from the response

            # Parsing the JSON string within the message content
            try:
                character_data = json.loads(message_content)
                print("Character data parsed successfully:", character_data)
                return character_data  # Return both character data and chat ID
            except json.JSONDecodeError:
                print("Failed to decode character data:", message_content)
                return None  # Return None for character data and the chat ID
        else:
            print("No choices found in response.")
            return None  # Return None for character data and indicate no ID found

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

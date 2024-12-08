import json
import os
from typing import Any, Coroutine

from dotenv import load_dotenv
from openai import OpenAI
from openai.resources.chat.completions import ChatCompletion
from pydantic import BaseModel

from app.db.db import Character

load_dotenv()


class CharacterUpdateInput(BaseModel):
    description: str | None = None
    name: str | None = None
    generated_traits: dict | None = None
    story_context: str | None = None

    def __repr__(self):
        return f"{self.description} {self.name} {self.generated_traits} {self.story_context}"


class Step(BaseModel):
    explanation: str
    output: str


class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str


async def generate_character_with_openai(character_data: Character) -> Any:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
   You are a creative AI assistant specialized in storytelling and character creation for children's stories. Please refine and enhance the provided elements to develop characters that are engaging, educational, and suitable for young readers:

- **Name**: Generate a fun and memorable name that resonates with young audiences.
- **Description**: Enhance the description to include lively and colorful details that paint a vivid picture of the character for children.
- **Traits**: Update the provided traits in a JSON-formatted dictionary. Each trait should be described in a way that is easy for children to understand and see reflected in the character's actions and decisions within the story:
  - **Curious**: Explain how this trait leads the character to discover magical or educational adventures.
  - **Brave**: Highlight how bravery helps the character overcome fears and achieve goals in a fun way.
  - **Sympathetic**: Describe how this trait makes the character a good friend or helper to others in the story.
  - **Cunning**: Show how cleverness is used for problem-solving in exciting or humorous situations.
  - **Resolute**: Emphasize the character’s perseverance in a way that teaches persistence and determination.
- **Story Context**: Provide a simple, engaging context that sets the stage for the character's adventures, suitable for a child's imagination and understanding.


Given Data:
- Description: "{character_data.character_description}"
- Name: "{character_data.character_name}"
- Traits: "{character_data.character_traits}"
- Story Context: "{character_data.character_story_context}"

**Important Guidelines**:
1. Enhancements should be suitable for children, focusing on clarity, fun, and educational value.
2. All responses must be in English, regardless of the original input language.
3. Format your response as a JSON object with the following structure:
```json
{{
  "optimized_name": "Suggested new name",
  "optimized_description": "Colorful and engaging description for children",
  "optimized_traits": {{
 "curious": "Describes how curiosity leads to fun and learning.",
    "brave": "Shows how bravery is fun and rewarding.",
    "sympathetic": "Illustrates the character's kindness and helpful nature.",
    "cunning": "Highlights clever ways the character solves problems.",
    "resolute": "Shows how determination helps the character overcome challenges."
  }},
  "optimized_story_context": "Engaging and simple setting that sparks children’s imaginations."
}}
"""
    try:

        response : ChatCompletion = client.chat.completions.create(
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
                "type": "json_object",
            },
            # This is an example; adjust based on actual API requirements
            model="gpt-4o-mini",
        )
        print(response)

        if response.choices:
            choice = response.choices[0]
            message_content = choice.message.content
            print("Message content:", json.loads(message_content))
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

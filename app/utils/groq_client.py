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
    prompt = chain_of_thoughts_char_prompt(character_data)

    try:
        response = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative AI assistant specialized in storytelling and character creation for children's stories.",
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


def zero_shot_character_details_prompt(character_data: Character) -> str:
    prompt = f"""
 Please refine and enhance the provided elements to develop characters that are engaging, educational, and suitable for young readers:

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
    return prompt


def few_shot_character_details_prompt(character_data: Character) -> str:
    prompt = f"""
Please refine and enhance the provided elements to develop characters that are engaging, educational, and suitable for young readers:

Task Description:
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

Example of a completed character transformation:
- Original Name: "Mr. Whiskers"
- New Name: "Captain Whiskerbeard"
- Original Description: "A cat with a penchant for high seas adventure."
- Enhanced Description: "Captain Whiskerbeard, the daring seafaring cat, sports a majestic beard and a gleaming eye-patch as he sails the candy-colored seas."
- Original Traits: "{{\\"curious\\": \\"loves exploring new waters\\", \\"brave\\": \\"never shies away from a storm\\", \\"sympathetic\\": \\"always rescues stranded sailors\\", \\"cunning\\": \\"navigates using the stars\\", \\"resolute\\": \\"determined to find the mythical Fish Island\\"}}"
- Enhanced Traits: {{
  "curious": "His insatiable curiosity for the unknown leads Captain Whiskerbeard to hidden underwater cities and mysterious floating islands.",
  "brave": "Bravely facing giant waves and scary sea monsters, Captain Whiskerbeard always steers his ship, the Star Whisker, to safety.",
  "sympathetic": "He is a hero to all sea creatures, big and small, rescuing them from nets and guiding them to safe waters.",
  "cunning": "Using his wits and knowledge of the sea, Captain Whiskerbeard often outsmarts the greedy Pirate Paws and his crew.",
  "resolute": "No storm, nor mythical creature can deter him from his quest to chart all of the magical waters of the world."
}}
- Original Story Context: "Mr. Whiskers embarks on a journey across the Great Blue Ocean."
- Optimized Story Context: "Captain Whiskerbeard's adventure takes him through the sparkling waters of the Sugar Sea, where islands made of candy cane and chocolate await explorers."

Important Guidelines:
1. Enhancements should be suitable for children, focusing on clarity, fun, and educational value.
2. All responses must be in English, regardless of the original input language.
3. Format your response as a JSON object with the following structure:
```json
{{
  "optimized_name": "Suggested new name",
  "optimized_description": "Colorful and engaging description for children",
  "optimized_traits":{{
    "curious": "Describes how curiosity leads to fun and learning.",
    "brave": "Shows how bravery is fun and rewarding.",
    "sympathetic": "Illustrates the character's kindness and helpful nature.",
    "cunning": "Highlights clever ways the character solves problems.",
    "resolute": "Shows how determination helps the character overcome challenges."
  }},
  "optimized_story_context": "Engaging and simple setting that sparks children’s imaginations."
}}
"""
    return prompt


def chain_of_thoughts_char_prompt(character_data: Character) -> str:
    prompt = (
        f"""
Please refine and enhance the provided elements to develop characters that are engaging, educational, and suitable for young readers by following a reasoned, step-by-step process:

1. **Name Generation**:
   - **Given Name**: "{character_data.character_name}"
   - **Task**: Generate a fun and memorable name that resonates with young audiences.
   - **Reasoning**: Consider what makes a name catchy and appealing to children. It should be easy to pronounce, fun to say, and reflect the character’s nature.

2. **Description Enhancement**:
   - **Given Description**: "{character_data.character_description}"
   - **Task**: Enhance the description to include lively and colorful details that paint a vivid picture of the character for children.
   - **Reasoning**: Think about what visual and emotional elements will capture the imagination of a child. Use vivid, sensory language that is engaging and evocative.

3. **Traits Update**:
   - **Given Traits**: "{character_data.character_traits}"
   - **Task**: Update the provided traits in a JSON-formatted dictionary. Each trait should be described in a way that is easy for children to understand and see reflected in the character’s actions and decisions within the story.
   - **Reasoning Steps**:
     - **Curious**: How does this trait lead the character to discover magical or educational adventures?
     - **Brave**: How does bravery help the character overcome fears and achieve goals in a fun way?
     - **Sympathetic**: How does this trait make the character a good friend or helper to others in the story?
     - **Cunning**: How is cleverness used for problem-solving in exciting or humorous situations?
     - **Resolute**: How does perseverance teach persistence and determination?

4. **Story Context Enhancement**:
   - **Given Story Context**: "{character_data.character_story_context}"
   - **Task**: Provide a simple, engaging context that sets the stage for the character's adventures, suitable for a child’s imagination and understanding.
   - **Reasoning**: What kind of setting will intrigue children and spark their imagination? Consider settings that are both fantastical and relatable to young minds.

**Final Output**:
Compile the refined character name, description, traits, and story context into a well-structured JSON object:
```json
{{
  "optimized_name": "Suggested new name",
  "optimized_description": "Colorful and engaging description for children",
  "optimized_traits": {{
    "curious": "Describes how curiosity leads to fun and learning adventures.",
    "brave": "Shows how bravery is fun and rewarding.",
    "sympathetic": "Illustrates the character's kindness and helpful nature.",
    "cunning": "Highlights clever ways the character solves problems.",
    "resolute": "Shows how determination helps the character overcome challenges."
  }},
  "optimized_story_context": "Engaging and simple setting that sparks children’s imaginations."
}}
"""
        ""
    )
    return prompt

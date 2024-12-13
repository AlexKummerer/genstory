import json
import os
from typing import Any, Coroutine, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
import openai
from openai.resources.chat.completions import ChatCompletion
from pydantic import BaseModel
from sqlalchemy import Sequence

from app.db.db import Character, Story

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
    prompt = structured_char_prompt(character_data)

    try:

        response: ChatCompletion = client.chat.completions.create(
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


async def generate_story_details_with_openai(
    story: Story, characters: List[Character]
) -> dict:

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    character_descriptions = "\n".join(
        f"- Name : {c.character_name}, Description {c.character_description}, Traits: {c.character_traits}, Story Context:  {c.character_story_context}"
        for c in characters
    )

    prompt = f"""
    Refine the following story details and enhance the narrative elements. Return your response in a JSON object format, ensuring each component is thoughtfully improved:

- **Title**: Provide a more captivating and relevant title that reflects the theme and intrigue of the story.
- **Description**: Expand the story description to include more detailed and vivid elements that capture the essence of the plot and setting. Make sure the description is engaging and sets the tone for the story.
- **Characters**: Provide each character and suggest key roles and enhancements for their descriptions in a json formatted dictionary. Describe how each character contributes to the story and their relationships with other characters. Based on the provided character descriptions, enhance their personalities, traits, and dynamics to make them more compelling and relatable to young readers.

Given Data:
- Title: "{story.title}"
- Description: "{story.description}"
- Characters:
  - {character_descriptions}

**Important Guidelines**:
1. Enhancements should be creative, detailed, and align with the theme of the story.
2. All responses must be in English.
3. Format your response as a JSON object with the following structure:

```json
{{
  "optimized_title": "Enhanced title that captures the essence of the story",
  "optimized_description": "Detailed and expanded description providing a deeper insight into the plot and setting",
  "character_roles":
    {{
      "name": "Character Name",
      "role": "Described role and key contributions to the story",
      "enhanced_description": "Expanded character description highlighting personality traits and dynamics with other characters"
      "skills": {{
          "curiousity": "Describes how curiosity leads to fun and learning.",
          "empathy": "Shows how empathy helps the character understand others' feelings.",
          "bravery": "Highlights how bravery is fun and rewarding.",
          "cunning": "Illustrates the character's imaginative and inventive nature.",
          resolution: "Shows how determination helps the character overcome challenges."
          }}
    }},
    {{
      "name": "Another Character Name",
      "role": "Described role and key contributions to the story",
      "enhanced_description": "Expanded character description highlighting personality traits and dynamics with other characters"
     "skills": {{
          "curiousity": "Describes how curiosity leads to fun and learning.",
          "empathy": "Shows how empathy helps the character understand others' feelings.",
          "bravery": "Highlights how bravery is fun and rewarding.",
          "cunning": "Illustrates the character's imaginative and inventive nature.",
          resolution: "Shows how determination helps the character overcome challenges."
          }}
    }}
}}"""
    try:

        response: ChatCompletion = client.chat.completions.create(
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

            # Parsing the JSON string within the message content
            try:
                character_data = json.loads(message_content)
                print("Character data parsed successfully:", character_data)
                return character_data
            except json.JSONDecodeError:
                print("Failed to decode character data:", message_content)
                return {}  # Return an empty dictionary instead of None
        else:
            print("No choices found in response.")
            return {}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}


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


def structured_char_prompt(character_data: Character) -> str:
    prompt = f"""
{{
  "instructions": "Transform the provided basic character elements into vibrant, educational characters suitable for young readers. Follow the structured steps below and use the accompanying example to guide your enhancements.",
  "example": {{
    "original": {{
      "name": "Mr. Whiskers",
      "description": "A curious cat who loves adventures at sea.",
      "traits": {{
        "curious": "Explores new waters",
        "brave": "Faces any storm",
        "sympathetic": "Helps stranded sailors",
        "cunning": "Navigates by stars",
        "resolute": "Seeks mythical lands"
      }},
      "story_context": "Sets sail across the vast ocean."
    }},
    "enhanced": {{
      "name": "Captain Whiskerbeard",
      "description": "The daring Captain Whiskerbeard, with a majestic beard and eye-patch, sails the candy-colored seas.",
      "traits": {{
        "curious": "Discovers hidden underwater cities",
        "brave": "Battles sea monsters courageously",
        "sympathetic": "Rescues all sea creatures",
        "cunning": "Outsmarts rival pirates",
        "resolute": "Never veers off his quest for magical waters"
      }},
      "story_context": "His journey through the Sugar Sea leads to candy cane islands and chocolate mountains."
    }}
  }},
  "tasks": [
    {{
      "name_generation": {{
        "given_name": "{character_data.character_name}",
        "task": "Create a memorable and catchy name suitable for a child's hero.",
        "reasoning": "A catchy name that is easy to remember and pronounce can greatly appeal to children and make the character more relatable."
      }}
    }},
    {{
      "description_enhancement": {{
        "given_description": "{character_data.character_description}",
        "task": "Enrich the description with vivid and engaging details.",
        "reasoning": "Vivid descriptions capture a child's imagination, making the character more real and engaging."
      }}
    }},
    {{
      "traits_update": {{
        "given_traits": "{character_data.character_traits}",
        "task": "Expand on each trait to show how they influence the character's adventures and interactions.",
        "reasoning_steps": [
          {{
            "curious": "Detail how curiosity drives the character to exciting discoveries.",
            "brave": "Explain how bravery helps face challenges.",
            "sympathetic": "Describe acts of kindness that endear the character to others.",
            "cunning": "Showcase clever solutions to tricky situations.",
            "resolute": "Illustrate steadfast determination in pursuing goals."
          }}
        ]
      }}
    }},
    {{
      "story_context_enhancement": {{
        "given_story_context": "{character_data.character_story_context}",
        "task": "Craft a captivating setting that ignites a child's fantasy and sense of adventure.",
        "reasoning": "An imaginative setting enhances the story's appeal and helps in delivering educational content in an entertaining way."
      }}
    }}
  ],
  "final_output": {{
    "task": "Compile the refined character elements into a structured JSON object that can be easily understood and utilized.",
    "example": {{
      "optimized_name": "Suggested new name",
      "optimized_description": "Colorful and engaging description for children",
      "optimized_traits": {{
        "curious": "Leads to educational adventures.",
        "brave": "Demonstrates overcoming fears.",
        "sympathetic": "Encourages empathy among young readers.",
        "cunning": "Teaches problem-solving skills.",
        "resolute": "Inspires persistence in pursuing dreams."
      }},
      "optimized_story_context": "Creates an engaging world that sparks imagination."
    }}
  }}
}}
"""

    return prompt

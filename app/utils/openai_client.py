import json
import os
from typing import Any, Coroutine, List, Optional, Dict

from dotenv import load_dotenv
from openai import OpenAI
import openai
from openai.resources.chat.completions import ChatCompletion

from openai.resources.beta.chat.completions import ParsedChatCompletion
from pydantic import BaseModel
from sqlalchemy import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.models import Character, Story
from app.schemas.traits import Trait


load_dotenv()


class EnhancedCharacter(BaseModel):
    optimized_name: str
    optimized_description: str
    optimized_traits: List[Trait]
    optimized_story_context: str


class CharacterUpdateInput(BaseModel):
    description: str | None = None
    name: str | None = None
    generated_traits: dict | None = None
    story_context: str | None = None

    def __repr__(self):
        return f"{self.description} {self.name} {self.generated_traits} {self.story_context}"


async def generate_character_with_openai(character_data: Character) -> Dict[str, Any]:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = structured_char_prompt(character_data)

    try:

        response = client.beta.chat.completions.parse(
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
            response_format=EnhancedCharacter,
            # This is an example; adjust based on actual API requirements
            model="gpt-4o-mini",
        )
        print(response)

        if not response.choices:
            raise ValueError("No choices found Open Ai response")

        result = response.choices[0].message.content
        parsed_response = json.loads(result)

        return parsed_response
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
Refine the following story details based on the examples provided. Return your response in a JSON object format, ensuring each component is thoughtfully improved:

### Example 1
- **Original Title**: "Ocean Adventures"
- **Original Description**: "A young sailor ventures into uncharted waters."
- **Characters**: 
  - Name: Sam, Description: "Curious young sailor", Traits: {{"curiosity": "high", "bravery": "moderate"}}, Story Context: "Exploring the Pacific."
- **Enhanced Title**: "Mysteries of the Deep"
- **Enhanced Description**: "Sam, the brave young sailor, faces mythical creatures and discovers lost underwater cities in the vast Pacific."
- **Enhanced Characters**:
  - Name: Sam, Role: "Protagonist", Enhanced Description: "Sam's insatiable curiosity and bravery lead him to mythical discoveries.", Skills: {{"curiosity": "leads to hidden treasures", "bravery": "fights sea monsters"}}
- **Reasoning**: The title and description are enhanced to reflect the adventurous and mythical elements of the story, which are likely to captivate young readers. Sam's traits of curiosity and bravery are emphasized to show his role in the narrative.

### Example 2
- **Original Title**: "Forest Whisperers"
- **Original Description**: "Two friends uncover secrets of the enchanted forest."
- **Characters**:
  - Name: Ela, Description: "Wise and old", Traits: {{"wisdom": "very high", "kindness": "high"}}, Story Context: "Guiding through mystical woods."
- **Enhanced Title**: "Echoes of the Ancient Woods"
- **Enhanced Description**: "Ela and her friend navigate through mystical woods, uncovering ancient secrets and forming alliances with magical creatures."
- **Enhanced Characters**:
  - Name: Ela, Role: "Guide", Enhanced Description: "Ela uses her wisdom and kindness to protect and guide her friends through dangers of the enchanted forest.", Skills: {{"wisdom": "solves ancient puzzles", "kindness": "earns trust of forest spirits"}}
- **Reasoning**: Enhancements focus on the magical and mysterious aspects of the forest. Ela's character is developed to highlight her wisdom and kindness, essential for guiding through mystical settings and engaging young readers.

### New Task
Given Data for Enhancement:
- **Title**: "{story.title}"
- **Description**: "{story.description}"
- **Characters**:
  {character_descriptions}

**Chain of Thought Approach**:
1. **Title Enhancement**:
   - **Current Title Analysis**: Reflect on how the existing title connects with the story's theme.
   - **Task**: Generate a title that is both intriguing and reflective of the adventure or mystery within the story.

2. **Description Enhancement**:
   - **Detailed Scene Setting**: Consider elements that make the story more vivid and engaging.
   - **Task**: Expand the description to include sensory details that paint a richer picture of the environment and action.

3. **Character Enhancement**:
   - **Character Contribution Review**: Assess how each character's traits and actions contribute to the story's progress.
   - **Task**: Suggest detailed roles for each character, enhancing their descriptions to better fit their contributions and relationships within the story.

**Output the refined elements in a structured JSON object**:
```json
{{
  "optimized_title": "Suggested new title",
  "optimized_description": "Enhanced description providing a deeper insight into the plot and setting",
  "character_roles": [
    {{
      "name": "Character Name",
      "role": "Suggested role and key contributions",
      "enhanced_description": "Expanded personality traits and dynamics",
      "skills": {{
        "curiosity": "Describes how curiosity leads to fun and educational adventures.",
        "empathy": "Shows how empathy helps the character understand others' feelings.",
        "bravery": "Highlights how bravery assists in overcoming challenges.",
        "cunning": "Illustrates clever solutions to problems faced.",
        "resolution": "Emphasizes persistence in achieving goals."
      }}
    }}]
  
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


async def generate_story_content(story: Story) -> List[str]:

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
Given the refined inputs for a middle story, generate a narrative that is engaging, educational, and suitable for young readers, formatted as a sequence of sentences for a digital storybook. Each sentence should advance the narrative and be fit for displaying one at a time.

### Inputs:
- **Title**: "{story.title}"
- **Description**: "{story.description}"
- **Characters**:
  {story.character_roles}  # Assuming character_roles is a list or description that explains each character's role.

### Task:
Craft a middle story using the inputs provided, ensuring that the narrative is educational, follows a logical sequence of events, and is displayed in a format suitable for digital storybooks:

1. **Opening**: Set the scene based on the overall description. Introduce the main characters and the initial situation, making sure it captures the reader’s imagination.
2. **Conflict**: Introduce a problem or challenge that the characters need to address or resolve, ensuring that this section includes elements that contribute to the story’s educational value.
3. **Progression**: Detail the characters' efforts to resolve the conflict, emphasizing their interactions, the roles they play, and key events and turning points that provide learning opportunities.
4. **Climax**: Lead the story to its most intense point where the outcome of the conflict is uncertain, while maintaining a child-friendly tone.
5. **Resolution**: Conclude the story by resolving the conflict and reflecting on the outcome and any lessons learned, aligning with the story's educational themes.

### Examples and Chain of Thought Process:
Here are examples of how each part of the story could be structured:

#### Example 1:
- **Title**: "The Quest for the Mystic Orb"
- **Opening**: "In the enchanted realm of Silvaria, young mage Lora discovers a map to the lost Mystic Orb."
- **Conflict**: "The orb is believed to be hidden in the depths of the Shadow Forest, guarded by the ancient tree spirits."
- **Progression**: "Lora, joined by her friend Riko, the inventor, navigates the forest, deciphering clues and overcoming magical barriers."
- **Climax**: "They find the orb protected under a spell, which requires them to solve a puzzle showing the importance of teamwork and wisdom."
- **Resolution**: "The spell breaks when they work together, highlighting the lesson that combined strengths bring greater success."

#### New Task:
Using the framework provided by the examples, develop your story by applying the same chain of thought to each segment:

```json
{{
  "sentences": [
    "Begin by setting the scene based on your overall description, introducing an imaginative setting.",
    "Introduce your main characters and describe the initial problem or challenge they face.",
    "Detail how the characters interact, learn, and begin to tackle the problem, incorporating educational elements.",
    "Describe the climax where the tension or stakes are highest, focusing on how the characters apply their learned skills.",
    "Resolve the conflict and conclude with a reflective ending that reinforces the educational theme."
  ]
}}
"""
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
                story_content = json.loads(message_content["sentences"])
                print("Character data parsed successfully:", story_content)
                return story_content
            except json.JSONDecodeError:
                print("Failed to decode character data:", message_content)
                return {}  # Return an empty dictionary instead of None
        else:
            print("No choices found in response.")
            return {}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}


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
        "task": "Expand on each trait to show how they influence the character's adventures and interactions. 
        "reasoning_steps": [
          If there are no traits given, create 3 - 5 new ones. base on the optimized description",
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

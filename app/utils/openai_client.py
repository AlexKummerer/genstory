import json
import os
from typing import Any, Coroutine, List, Optional, Dict

from dotenv import load_dotenv
from openai import OpenAI

from openai.resources.chat.completions import ChatCompletion
from openai.resources.images import ImagesResponse

from openai.resources.beta.chat.completions import ParsedChatCompletion
from pydantic import BaseModel
from sqlalchemy import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.models import Character, Story
from app.schemas.traits import Trait


load_dotenv()


class Skill(BaseModel):
    skill_name: str  # Name of the skill (e.g., curiosity, bravery)
    skill_description: (
        str  # Description of the skill and how it contributes to the story
    )


class CharacterRole(BaseModel):
    name: str
    role: str
    enhanced_description: str
    skills: List[Skill]  # List of skills instead of a dictionary
    motivations: str
    flaws: str
    interactions: str


class Test(BaseModel):
    test_name: str
    description: str


class MiddleSection(BaseModel):
    setting_out: str
    encounter_with_challenges: str
    tests: List[Test]


class StoryStructure(BaseModel):
    introduction: str
    middle: MiddleSection  # Structured middle as per requirements
    climax: str
    conclusion: str
    lessons: List[str]


class FullStoryDetails(BaseModel):
    story_structure: StoryStructure
    full_story: str


class EnhancedStoryDetails(BaseModel):
    optimized_title: str
    optimized_description: str
    character_roles: List[CharacterRole]


class EnhancedStory(BaseModel):
    enhanced_details: EnhancedStoryDetails
    story_details: FullStoryDetails


class EnhancedCharacter(BaseModel):
    optimized_name: str
    optimized_description: str
    optimized_traits: List[Trait]
    optimized_story_context: str


class CoverImagePrompt(BaseModel):
    prompt: str


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

        if not response.choices:
            raise ValueError("No choices found Open Ai response")

        result = response.choices[0].message.content
        parsed_response = json.loads(result)

        return parsed_response
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


async def generate_story_details_with_openai(
    story: Story, characters: List[Character]
) -> dict:

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = story_details_prompt(characters, story)

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
            response_format=EnhancedStoryDetails,
            # This is an example; adjust based on actual API requirements
            model="gpt-4o-mini",
        )

        if not response.choices:
            raise ValueError("No choices found Open Ai response")

        result = response.choices[0].message.content
        parsed_response = json.loads(result)

        return parsed_response
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}


async def generate_story_content(story: Story) -> EnhancedStory:

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = story_content_prompt(story)

    try:

        response: ChatCompletion = client.beta.chat.completions.parse(
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
            response_format=FullStoryDetails,
            # This is an example; adjust based on actual API requirements
            model="gpt-4o-mini",
        )

        if not response.choices:
            raise ValueError("No choices found Open Ai response")

        result = response.choices[0].message.content
        parsed_response = json.loads(result)

        return parsed_response
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}


def generate_cover_image_prompt(story: Story) -> str:

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Narrative-style meta-prompt
    meta_prompt_narrative = f"""
Using the following full story as input, craft a vivid, narrative-style prompt for an AI image generator to create a magical, storybook-like cover illustration.



Full Story:
{story.content["full_story"]}

Focus on depicting a single, climactic moment that captures the heart of the story. Your description should vividly bring the scene to life, incorporating:

The illustration should capture a single, climactic moment that conveys the heart of the story, bringing it to life with rich, imaginative details. Focus on creating an image that appeals to child and evokes a sense of wonder and adventure.

Include the following:

Setting: Describe the environment in intricate detail, emphasizing magical or whimsical elements, atmospheric lighting, and textures that align with the story’s adventurous tone.
Characters: Paint a vivid picture of the characters—their appearance, actions, and emotional expressions—highlighting their interaction and bond.
Action or Dynamic Interaction: Show movement, dramatic tension, or an emotional highlight to bring the scene to life.
Perspective and Composition: Suggest a dynamic composition, such as a close-up of the characters or a wide-angle that incorporates the environment and action.
Themes and Symbolism: Reflect key themes, such as friendship, bravery, and discovery, with symbolic elements (e.g., a glowing tree as a beacon of guidance).
Mood and Emotional Tone: Clearly capture the mood (e.g., adventurous, comforting, or triumphant) with specific lighting and color palettes.
Art Style: Specify the desired art style, such as whimsical and cartoonish, soft watercolor, or a vibrant storybook aesthetic.
Magical Enhancements: Incorporate fantastical elements, like glowing butterflies, shimmering leaves, or enchanted lighting effects, to amplify the magic.
Scalability for Text: Ensure space is left for the story’s title and author name, if needed, without crowding the focal point.
Output the description as a single, cohesive paragraph, using immersive, narrative-driven language that feels inspiring and guides the artist in visualizing the scene.
"""

    try:

        response: ChatCompletion = client.beta.chat.completions.parse(
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative assistant skilled in crafting vivid, narrative-style prompts for visual storytelling.",
                },
                {
                    "role": "user",
                    "content": meta_prompt_narrative,
                },
            ],
            response_format=CoverImagePrompt,
            # This is an example; adjust based on actual API requirements
            model="gpt-4o-mini",
        )

        if not response.choices:
            raise ValueError("No choices found Open Ai response")

        result = response.choices[0].message.content
        parsed_response = json.loads(result)

        return parsed_response
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}


def generate_cover_image(cover_image_prompt: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response: ImagesResponse = client.images.generate(
            model="dall-e-3",
            prompt=cover_image_prompt,
            size="1024x1024",
            quality="hd",
            style="vivid",
            response_format="b64_json",
            n=1,
        )

        if not response.data:
            raise ValueError("No data found in Open Ai response")
        return response.data[0].b64_json

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


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


def story_details_prompt(characters: List[Character], story: Story) -> str:
    character_descriptions = "\n".join(
        f"- Name: {c.character_name}, Description: {c.character_description}, Traits: {c.character_traits}, Story Context: {c.character_story_context}"
        for c in characters
    )

    prompt = f"""
You are a storytelling assistant specialized in creating engaging and educational narratives. Refine the following story details and provide enhancements in a structured JSON format.

### Input Details
- **Title**: "{story.title}"
- **Description**: "{story.description}"
- **Characters**:
{character_descriptions}

### Output Requirements
1. **Optimized Title**:
   - Provide a refined version of the title that is captivating, relevant to the story's theme, and sparks curiosity.

2. **Optimized Description**:
   - Enhance the story description with vivid imagery and engaging elements. Include sensory details that make the plot and setting more immersive for readers.

3. **Character Roles**:
   - For each character, refine their details and clearly define their role in the story. Include:
     - **Name**: Character’s name.
     - **Role**: Their purpose and contributions to the narrative (e.g., Protagonist, Mentor).
     - **Enhanced Description**: Detailed traits and unique characteristics.
     - **Skills**: List their abilities, including:
       - **Curiosity**: How curiosity aids their role.
       - **Empathy**: How empathy influences their actions.
       - **Bravery**: How bravery helps them overcome challenges.
       - **Cunning**: How cleverness aids in problem-solving.
       - **Resolution**: How persistence helps achieve goals.
     - **Motivations**: What drives their actions and decisions.
     - **Flaws**: Weaknesses or limitations that create depth and relatability.
     - **Interactions**: How they interact with other characters and influence the story.

4. **Reasoning**:
   - For each enhancement (title, description, character roles), provide a brief explanation of why the changes improve the narrative.

### Example Output
```json
{{
  "optimized_title": "The Enchanted Forest Quest",
  "optimized_description": "A magical journey through a vibrant forest where teamwork and bravery unlock hidden mysteries.",
  "character_roles": [
    {{
      "name": "Lila",
      "role": "Protagonist",
      "enhanced_description": "Lila is a curious and brave young girl who embarks on a journey to save her village from a mysterious curse. Her determination and resourcefulness make her a natural leader.",
      "skills": [
        {{"name": "Curiosity", "description": "Helps her discover hidden clues and magical pathways."}},
        {{"name": "Bravery", "description": "Enables her to face challenges and overcome her fears."}}
      ],
      "motivations": "To lift the curse and protect her family and friends.",
      "flaws": "Her impulsive nature sometimes leads to risky decisions.",
      "interactions": "Lila forms a close bond with the forest creatures, who guide her on her journey. She learns to rely on her friends and appreciate teamwork."
    }},
    {{
      "name": "Elder Oak",
      "role": "Mentor",
      "enhanced_description": "A wise and ancient tree spirit who knows the secrets of the forest. Elder Oak provides guidance and imparts valuable lessons to Lila.",
      "skills": [
        {{"name": "Wisdom", "description": "Provides insights to solve riddles and avoid danger."}},
        {{"name": "Magic", "description": "Uses his powers to protect Lila when she is in danger."}}
      ],
      "motivations": "To preserve the forest’s harmony and help Lila fulfill her destiny.",
      "flaws": "He speaks in riddles, which sometimes confuses Lila and slows her progress.",
      "interactions": "Elder Oak mentors Lila, helping her unlock her potential and teaching her the importance of patience and understanding."
    }}
  ],
  "reasoning": {{
    "title": "The refined title emphasizes the quest and mystery elements, making it more engaging for readers.",
    "description": "The enhanced description adds sensory details and emotional depth, capturing the reader's imagination.",
    "character_roles": "Each character’s role is clearly defined, making their contribution to the story cohesive and compelling."
  }}
}}"""

    return prompt


def story_content_prompt(story: Story) -> str:

    thought_process = f"""
 Step 1: Introduce the main characters ({', '.join([c["name"] for c in story.character_roles])}) and describe tgeir personalities, motivations, to the magical setting.
 Step 2: Set up the magical world described in the story and hint at the mystery or challenge that the characters will face.
 Step 3: Introduce the conflit or obstacle that will drive the story forward, and highlight how the characters will need to work together to overcome it.
 Step 4 : Develop the story by detailing the characters' journey, including the challenges they face, the lessons they learn, and the friendships they form.
  Step 5: Reach the climax of the story, where the characters face their greatest challenge and must use their skills and strengths to succeed.
  Step 6: Conclude the story by resolving the conflict, highlighting the characters' growth and the lessons they have learned adn the rewards of their journey.
    """

    prompt = f"""
    You are a famouse children's book author and you are tasked with creating a middle story for a children's book. The story should be engaging, educational, and suitable for young readers. Write a complete story titled "{story.title}" bassed on the following description and characters:
    
    ### Description:
    {story.description}
    
    ### Characters:

  {story.character_roles}  # Assuming character_roles is a list or description that explains each character's role.
  
  Here is a chain of thought process to guide you through the story development:
  {thought_process}
  
  The story should be imaginative, playfule and suitable for children aged 6 - 10. Use vivid descriptions, engaging dialogue, and a child-friendly tone to captivate young readers. Ensure the story has a clear introduction, middle and resolution with lessons or morals that are relevant to the characters' journey.
  """

    return prompt

# Phase 1 Implementation Guide: Backend Enhancements

## Overview

Phase 1 focuses on transforming the GenStoryAI backend from a simple story generator into a sophisticated, scene-based storytelling platform with iterative refinement capabilities and multi-audience support. All enhancements will be API-only, requiring no frontend changes.

## Timeline: 4-5 Weeks

- **Weeks 1-2**: Enhanced Story Structure
- **Week 3**: Iterative Refinement System
- **Week 4**: Multi-Audience Support
- **Week 5**: Image Generation & Export Systems

## Week 1-2: Enhanced Story Structure

### Objective
Transform the current monolithic story content into a scene-based structure that supports better reading experiences and granular content management.

### Step 1: Database Schema Updates

#### 1.1 Create Migration File
```bash
alembic revision --autogenerate -m "add_scene_based_story_structure"
```

#### 1.2 Migration Content
```python
# alembic/versions/xxx_add_scene_based_story_structure.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add new columns to stories table
    op.add_column('stories', sa.Column('scenes', sa.JSON(), nullable=True))
    op.add_column('stories', sa.Column('target_audience', sa.String(50), nullable=True, default='children_6_10'))
    op.add_column('stories', sa.Column('genre', sa.String(50), nullable=True, default='adventure'))
    op.add_column('stories', sa.Column('total_reading_time', sa.Integer(), nullable=True))
    op.add_column('stories', sa.Column('total_word_count', sa.Integer(), nullable=True))
    op.add_column('stories', sa.Column('version', sa.Integer(), nullable=False, default=1))
    op.add_column('stories', sa.Column('refinement_count', sa.Integer(), nullable=False, default=0))
    op.add_column('stories', sa.Column('version_history', sa.JSON(), nullable=True))
    
    # Create new tables
    op.create_table('story_refinements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('story_id', sa.String(), nullable=False),
        sa.Column('scene_id', sa.String(), nullable=True),
        sa.Column('refinement_type', sa.String(50), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('before_content', sa.JSON(), nullable=True),
        sa.Column('after_content', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], )
    )
    
    op.create_table('story_images',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('story_id', sa.String(), nullable=False),
        sa.Column('scene_id', sa.String(), nullable=True),
        sa.Column('image_type', sa.String(20), nullable=False),
        sa.Column('base64_data', sa.Text(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], )
    )

def downgrade():
    op.drop_table('story_images')
    op.drop_table('story_refinements')
    op.drop_column('stories', 'version_history')
    op.drop_column('stories', 'refinement_count')
    op.drop_column('stories', 'version')
    op.drop_column('stories', 'total_word_count')
    op.drop_column('stories', 'total_reading_time')
    op.drop_column('stories', 'genre')
    op.drop_column('stories', 'target_audience')
    op.drop_column('stories', 'scenes')
```

### Step 2: Create Scene Models

#### 2.1 Scene Schema Models
```python
# app/schemas/scenes.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

class SceneType(str, Enum):
    INTRODUCTION = "introduction"
    RISING_ACTION = "rising_action"
    CLIMAX = "climax"
    FALLING_ACTION = "falling_action"
    CONCLUSION = "conclusion"

class Scene(BaseModel):
    scene_id: str = Field(..., description="Unique identifier for the scene")
    scene_number: int = Field(..., ge=1, description="Sequential scene number")
    type: SceneType = Field(..., description="Type of scene in story structure")
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=10)
    image_prompt: str = Field(..., description="Prompt for generating scene illustration")
    image_id: Optional[str] = Field(None, description="ID of generated image")
    characters_present: List[str] = Field(default_factory=list)
    estimated_reading_time: int = Field(..., ge=0, description="Estimated reading time in seconds")
    word_count: int = Field(..., ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "scene_id": "scene_1",
                "scene_number": 1,
                "type": "introduction",
                "title": "A Mysterious Discovery",
                "content": "Emma and her faithful companion Max...",
                "image_prompt": "Young girl with dog discovering magical portal",
                "characters_present": ["emma", "max"],
                "estimated_reading_time": 45,
                "word_count": 150
            }
        }

class StoryScenes(BaseModel):
    scenes: List[Scene]
    total_scenes: int
    total_reading_time: int
    total_word_count: int
```

#### 2.2 Update Story Models
```python
# app/db/models.py
# Add to existing imports
from sqlalchemy import JSON, Integer

# Update Story model
class Story(BaseModel):
    # ... existing fields ...
    
    # New fields
    scenes = Column(JSON, nullable=True)
    target_audience = Column(String(50), nullable=True, default='children_6_10')
    genre = Column(String(50), nullable=True, default='adventure')
    total_reading_time = Column(Integer, nullable=True)
    total_word_count = Column(Integer, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    refinement_count = Column(Integer, nullable=False, default=0)
    version_history = Column(JSON, nullable=True)
    
    def to_detailed_response(self):
        """Enhanced response with scene information"""
        base_response = self.to_response()
        base_response.update({
            'scenes': self.scenes,
            'target_audience': self.target_audience,
            'genre': self.genre,
            'total_reading_time': self.total_reading_time,
            'total_word_count': self.total_word_count,
            'version': self.version,
            'refinement_count': self.refinement_count
        })
        return base_response
```

### Step 3: Update Story Generation Logic

#### 3.1 Create Scene Parser
```python
# app/utils/scene_parser.py
import re
from typing import List, Dict, Any
from app.schemas.scenes import Scene, SceneType
import uuid

class SceneParser:
    """Parse story content into scenes"""
    
    WORDS_PER_MINUTE = 200  # Average reading speed
    
    @staticmethod
    def calculate_reading_time(text: str) -> int:
        """Calculate reading time in seconds"""
        word_count = len(text.split())
        minutes = word_count / SceneParser.WORDS_PER_MINUTE
        return int(minutes * 60)
    
    @staticmethod
    def parse_story_structure(story_content: Dict[str, Any]) -> List[Scene]:
        """Convert existing story structure to scenes"""
        scenes = []
        scene_number = 1
        
        # Parse introduction
        if 'introduction' in story_content['story_structure']:
            intro_content = story_content['story_structure']['introduction']
            scenes.append(Scene(
                scene_id=f"scene_{scene_number}",
                scene_number=scene_number,
                type=SceneType.INTRODUCTION,
                title="The Beginning",
                content=intro_content,
                image_prompt="",  # Will be generated
                characters_present=[],  # Will be extracted
                estimated_reading_time=SceneParser.calculate_reading_time(intro_content),
                word_count=len(intro_content.split())
            ))
            scene_number += 1
        
        # Parse middle section (tests/challenges)
        if 'middle' in story_content['story_structure']:
            middle = story_content['story_structure']['middle']
            
            # Setting out
            if 'setting_out' in middle:
                content = middle['setting_out']
                scenes.append(Scene(
                    scene_id=f"scene_{scene_number}",
                    scene_number=scene_number,
                    type=SceneType.RISING_ACTION,
                    title="Setting Out",
                    content=content,
                    image_prompt="",
                    characters_present=[],
                    estimated_reading_time=SceneParser.calculate_reading_time(content),
                    word_count=len(content.split())
                ))
                scene_number += 1
            
            # Each test/challenge
            if 'tests' in middle:
                for test in middle['tests']:
                    scenes.append(Scene(
                        scene_id=f"scene_{scene_number}",
                        scene_number=scene_number,
                        type=SceneType.RISING_ACTION,
                        title=test.get('test_name', f"Challenge {scene_number}"),
                        content=test.get('description', ''),
                        image_prompt="",
                        characters_present=[],
                        estimated_reading_time=SceneParser.calculate_reading_time(test.get('description', '')),
                        word_count=len(test.get('description', '').split())
                    ))
                    scene_number += 1
        
        # Parse climax
        if 'climax' in story_content['story_structure']:
            climax_content = story_content['story_structure']['climax']
            scenes.append(Scene(
                scene_id=f"scene_{scene_number}",
                scene_number=scene_number,
                type=SceneType.CLIMAX,
                title="The Climax",
                content=climax_content,
                image_prompt="",
                characters_present=[],
                estimated_reading_time=SceneParser.calculate_reading_time(climax_content),
                word_count=len(climax_content.split())
            ))
            scene_number += 1
        
        # Parse conclusion
        if 'conclusion' in story_content['story_structure']:
            conclusion_content = story_content['story_structure']['conclusion']
            scenes.append(Scene(
                scene_id=f"scene_{scene_number}",
                scene_number=scene_number,
                type=SceneType.CONCLUSION,
                title="The End",
                content=conclusion_content,
                image_prompt="",
                characters_present=[],
                estimated_reading_time=SceneParser.calculate_reading_time(conclusion_content),
                word_count=len(conclusion_content.split())
            ))
        
        return scenes
    
    @staticmethod
    def generate_scene_image_prompts(scenes: List[Scene], story_context: Dict) -> List[Scene]:
        """Generate appropriate image prompts for each scene"""
        for scene in scenes:
            # Extract key visual elements from the scene
            scene.image_prompt = SceneParser._create_image_prompt(
                scene.content,
                scene.type,
                story_context
            )
        return scenes
    
    @staticmethod
    def _create_image_prompt(content: str, scene_type: SceneType, context: Dict) -> str:
        """Create an image prompt based on scene content and type"""
        # This will be enhanced with proper prompt engineering
        base_style = "children's book illustration, whimsical, colorful"
        
        if scene_type == SceneType.INTRODUCTION:
            return f"{base_style}, establishing shot, {content[:100]}..."
        elif scene_type == SceneType.CLIMAX:
            return f"{base_style}, dramatic moment, action scene, {content[:100]}..."
        else:
            return f"{base_style}, {content[:100]}..."
```

#### 3.2 Update Story Content Generation
```python
# app/utils/openai_client.py
# Add to existing file

def structured_scene_prompt(story: Story, characters: List[Character]) -> str:
    """Generate prompt for scene-based story structure"""
    prompt = f"""
    Create a detailed story with the following structure, broken into clear scenes:
    
    Title: {story.title}
    Description: {story.description}
    Target Audience: {story.target_audience}
    Genre: {story.genre}
    
    Characters:
    {json.dumps([char.to_response() for char in characters], indent=2)}
    
    Please structure the story with:
    1. Introduction (1-2 scenes): Set up the world and introduce characters
    2. Rising Action (3-4 scenes): Build tension through challenges
    3. Climax (1-2 scenes): The peak of conflict/excitement
    4. Resolution (1 scene): Wrap up and lessons learned
    
    For each scene, provide:
    - A descriptive title
    - The scene content (150-300 words)
    - Which characters are present
    - A visual description suitable for illustration
    
    Ensure the language and themes are appropriate for {story.target_audience}.
    """
    return prompt

class SceneBasedStory(BaseModel):
    """Response format for scene-based stories"""
    introduction_scenes: List[Dict[str, str]]
    rising_action_scenes: List[Dict[str, str]]
    climax_scenes: List[Dict[str, str]]
    resolution_scenes: List[Dict[str, str]]
    full_story: str
    lessons: List[str]
```

### Step 4: Update Story Service

#### 4.1 Enhanced Story Service
```python
# app/services/story_service.py
# Add new imports
from app.utils.scene_parser import SceneParser
from app.schemas.scenes import StoryScenes

class StoryService:
    # ... existing methods ...
    
    @staticmethod
    async def create_story_content(story_id: str, user: User, db: AsyncSession):
        """Enhanced story content creation with scenes"""
        # Fetch the story
        query = select(Story).where(
            Story.id == story_id,
            Story.user_id == user.id,
        )
        result = await db.execute(query)
        story = result.scalars().first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found.")
        
        # Generate story content
        content = await generate_story_content(story)
        
        # Parse into scenes
        scenes = SceneParser.parse_story_structure(content)
        
        # Generate image prompts for scenes
        scenes = SceneParser.generate_scene_image_prompts(scenes, {
            'title': story.title,
            'characters': story.character_roles
        })
        
        # Calculate totals
        total_reading_time = sum(scene.estimated_reading_time for scene in scenes)
        total_word_count = sum(scene.word_count for scene in scenes)
        
        # Update story with scene data
        story.content = content
        story.scenes = [scene.dict() for scene in scenes]
        story.total_reading_time = total_reading_time
        story.total_word_count = total_word_count
        story.status = "finalized"
        story.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(story)
        return story.to_detailed_response()
```

## Week 3: Iterative Refinement System

### Step 5: Create Refinement Models

#### 5.1 Refinement Schemas
```python
# app/schemas/refinements.py
from typing import Literal, List, Optional
from pydantic import BaseModel, Field

class RefinementType(str, Enum):
    SIMPLIFY_LANGUAGE = "simplify_language"
    ADD_MORE_ACTION = "add_more_action"
    INCREASE_DIALOGUE = "increase_dialogue"
    ENHANCE_DESCRIPTIONS = "enhance_descriptions"
    STRENGTHEN_MORAL = "strengthen_moral"
    ADD_HUMOR = "add_humor"
    INCREASE_SUSPENSE = "increase_suspense"
    CUSTOM = "custom"

class RefinementRequest(BaseModel):
    refinement_type: RefinementType
    custom_instructions: Optional[str] = Field(None, max_length=500)
    preserve_elements: List[str] = Field(default_factory=list)
    target_length: Optional[Literal["shorter", "same", "longer"]] = "same"
    
class SceneRefinementRequest(RefinementRequest):
    scene_id: str

class StoryRefinementResponse(BaseModel):
    story_id: str
    version: int
    refinement_count: int
    changes_made: List[str]
    scenes: List[Scene]
```

### Step 6: Implement Refinement Service

#### 6.1 Create Refinement Service
```python
# app/services/refinement_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Story, StoryRefinement, User
from app.schemas.refinements import RefinementRequest, RefinementType
from app.utils.openai_client import refine_with_openai
import json
import uuid
from datetime import datetime

class RefinementService:
    
    REFINEMENT_PROMPTS = {
        RefinementType.SIMPLIFY_LANGUAGE: "Simplify the language to be more accessible for younger readers. Use shorter sentences and simpler vocabulary.",
        RefinementType.ADD_MORE_ACTION: "Add more action and excitement to the scene. Include dynamic verbs and thrilling moments.",
        RefinementType.INCREASE_DIALOGUE: "Add more character dialogue to make the scene more engaging. Show character personalities through their speech.",
        RefinementType.ENHANCE_DESCRIPTIONS: "Enhance the sensory descriptions. Add details about sights, sounds, smells, and feelings.",
        RefinementType.STRENGTHEN_MORAL: "Make the moral lesson clearer and more impactful without being preachy.",
        RefinementType.ADD_HUMOR: "Add age-appropriate humor and fun moments to make the story more entertaining.",
        RefinementType.INCREASE_SUSPENSE: "Build more suspense and tension. Create anticipation for what happens next."
    }
    
    @staticmethod
    async def refine_scene(
        story_id: str,
        scene_id: str,
        refinement_request: RefinementRequest,
        user: User,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Refine a specific scene"""
        # Get story
        story = await StoryService.get_story_by_id(story_id, user, db)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        # Find the specific scene
        scenes = story.scenes or []
        scene_index = next((i for i, s in enumerate(scenes) if s['scene_id'] == scene_id), None)
        
        if scene_index is None:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        original_scene = scenes[scene_index]
        
        # Create refinement prompt
        refinement_prompt = RefinementService._build_refinement_prompt(
            original_scene,
            refinement_request,
            story
        )
        
        # Call OpenAI for refinement
        refined_content = await refine_with_openai(refinement_prompt)
        
        # Update scene
        refined_scene = original_scene.copy()
        refined_scene['content'] = refined_content
        refined_scene['word_count'] = len(refined_content.split())
        refined_scene['estimated_reading_time'] = len(refined_content.split()) * 60 // 200
        
        # Store refinement history
        refinement_record = StoryRefinement(
            id=str(uuid.uuid4()),
            story_id=story_id,
            scene_id=scene_id,
            refinement_type=refinement_request.refinement_type,
            instructions=refinement_request.custom_instructions,
            before_content=original_scene,
            after_content=refined_scene,
            created_at=datetime.now()
        )
        db.add(refinement_record)
        
        # Update story
        scenes[scene_index] = refined_scene
        story.scenes = scenes
        story.refinement_count += 1
        story.version += 1
        
        # Add to version history
        version_history = story.version_history or []
        version_history.append({
            'version': story.version,
            'timestamp': datetime.now().isoformat(),
            'change_type': 'scene_refinement',
            'scene_id': scene_id,
            'refinement_type': refinement_request.refinement_type
        })
        story.version_history = version_history
        
        await db.commit()
        await db.refresh(story)
        
        return {
            'story_id': story_id,
            'scene_id': scene_id,
            'refined_scene': refined_scene,
            'version': story.version,
            'refinement_count': story.refinement_count
        }
    
    @staticmethod
    def _build_refinement_prompt(
        scene: Dict[str, Any],
        request: RefinementRequest,
        story: Story
    ) -> str:
        """Build refinement prompt for OpenAI"""
        base_prompt = f"""
        Please refine the following scene from a {story.genre} story for {story.target_audience}:
        
        Scene Title: {scene['title']}
        Scene Type: {scene['type']}
        Current Content:
        {scene['content']}
        
        Refinement Instructions:
        """
        
        if request.refinement_type != RefinementType.CUSTOM:
            base_prompt += RefinementService.REFINEMENT_PROMPTS[request.refinement_type]
        else:
            base_prompt += request.custom_instructions or "Improve the scene quality"
        
        if request.preserve_elements:
            base_prompt += f"\n\nPreserve these elements: {', '.join(request.preserve_elements)}"
        
        if request.target_length:
            length_instruction = {
                "shorter": "Make the scene 25% shorter",
                "same": "Keep the scene roughly the same length",
                "longer": "Make the scene 25% longer"
            }
            base_prompt += f"\n\n{length_instruction[request.target_length]}"
        
        base_prompt += "\n\nProvide only the refined scene content, maintaining the story's tone and continuity."
        
        return base_prompt
```

### Step 7: Create Refinement Endpoints

#### 7.1 Add Refinement Routes
```python
# app/api/stories.py
# Add to existing file

from app.schemas.refinements import (
    RefinementRequest, 
    SceneRefinementRequest,
    StoryRefinementResponse
)
from app.services.refinement_service import RefinementService

@router.post("/{story_id}/refine-scene/{scene_id}", response_model=Dict[str, Any])
async def refine_story_scene(
    story_id: str,
    scene_id: str,
    refinement_request: RefinementRequest,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Refine a specific scene in the story"""
    try:
        return await RefinementService.refine_scene(
            story_id, scene_id, refinement_request, user, db
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to refine scene: {str(e)}"
        )

@router.post("/{story_id}/refine-style", response_model=StoryRefinementResponse)
async def refine_story_style(
    story_id: str,
    refinement_request: RefinementRequest,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Refine the overall style of the story"""
    try:
        return await RefinementService.refine_story_style(
            story_id, refinement_request, user, db
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refine story style: {str(e)}"
        )

@router.get("/{story_id}/refinement-history")
async def get_refinement_history(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Get the refinement history for a story"""
    try:
        return await RefinementService.get_refinement_history(story_id, user, db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get refinement history: {str(e)}"
        )

@router.post("/{story_id}/revert/{version}")
async def revert_to_version(
    story_id: str,
    version: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Revert story to a previous version"""
    try:
        return await RefinementService.revert_to_version(
            story_id, version, user, db
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revert story: {str(e)}"
        )
```

## Week 4: Multi-Audience Support

### Step 8: Add Audience Types

#### 8.1 Create Audience Enums
```python
# app/schemas/audience.py
from enum import Enum
from typing import Dict, Any

class AudienceType(str, Enum):
    TODDLERS = "toddlers_2_4"
    YOUNG_CHILDREN = "children_5_7"
    MIDDLE_GRADE = "children_8_10"
    PRETEENS = "preteens_11_13"
    YOUNG_ADULTS = "ya_14_17"
    ADULTS = "adults_18_plus"

class GenreType(str, Enum):
    ADVENTURE = "adventure"
    FANTASY = "fantasy"
    MYSTERY = "mystery"
    EDUCATIONAL = "educational"
    COMEDY = "comedy"
    DRAMA = "drama"
    SCIFI = "scifi"
    HISTORICAL = "historical"

class AudienceConfig:
    """Configuration for different audience types"""
    
    CONFIGS = {
        AudienceType.TODDLERS: {
            "max_word_count": 500,
            "vocabulary_level": "very_simple",
            "sentence_length": "very_short",
            "themes": ["friendship", "family", "colors", "animals", "basic_emotions"],
            "complexity": "minimal",
            "illustrations_per_scene": 1
        },
        AudienceType.YOUNG_CHILDREN: {
            "max_word_count": 1500,
            "vocabulary_level": "simple",
            "sentence_length": "short",
            "themes": ["adventure", "friendship", "problem_solving", "imagination"],
            "complexity": "low",
            "illustrations_per_scene": 1
        },
        AudienceType.MIDDLE_GRADE: {
            "max_word_count": 3000,
            "vocabulary_level": "moderate",
            "sentence_length": "medium",
            "themes": ["adventure", "mystery", "friendship", "courage", "growth"],
            "complexity": "moderate",
            "illustrations_per_scene": 1
        },
        AudienceType.PRETEENS: {
            "max_word_count": 5000,
            "vocabulary_level": "advanced",
            "sentence_length": "varied",
            "themes": ["identity", "relationships", "challenges", "moral_dilemmas"],
            "complexity": "moderate_high",
            "illustrations_per_scene": 0.5
        },
        AudienceType.YOUNG_ADULTS: {
            "max_word_count": 8000,
            "vocabulary_level": "advanced",
            "sentence_length": "varied",
            "themes": ["romance", "identity", "social_issues", "coming_of_age"],
            "complexity": "high",
            "illustrations_per_scene": 0.3
        },
        AudienceType.ADULTS: {
            "max_word_count": 10000,
            "vocabulary_level": "sophisticated",
            "sentence_length": "varied",
            "themes": ["complex_relationships", "moral_ambiguity", "social_commentary"],
            "complexity": "high",
            "illustrations_per_scene": 0.2
        }
    }
    
    @classmethod
    def get_config(cls, audience_type: AudienceType) -> Dict[str, Any]:
        return cls.CONFIGS.get(audience_type, cls.CONFIGS[AudienceType.MIDDLE_GRADE])
```

#### 8.2 Update Story Input Schema
```python
# app/schemas/stories.py
# Update existing schema

from app.schemas.audience import AudienceType, GenreType

class StoryInput(BaseModel):
    title: Optional[str]
    description: str
    character_ids: List[str]
    target_audience: AudienceType = AudienceType.MIDDLE_GRADE
    genre: GenreType = GenreType.ADVENTURE
    
    # ... existing validators ...
```

### Step 9: Audience-Specific Prompts

#### 9.1 Create Prompt Builder
```python
# app/utils/audience_prompts.py
from app.schemas.audience import AudienceType, GenreType, AudienceConfig
from typing import Dict, Any

class AudiencePromptBuilder:
    """Build prompts tailored to specific audiences"""
    
    @staticmethod
    def build_story_prompt(
        title: str,
        description: str,
        characters: List[Dict],
        audience: AudienceType,
        genre: GenreType
    ) -> str:
        config = AudienceConfig.get_config(audience)
        
        prompt = f"""
        Create a {genre.value} story titled "{title}" for {audience.value.replace('_', ' ')}.
        
        Story Description: {description}
        
        Target Audience Requirements:
        - Vocabulary Level: {config['vocabulary_level']}
        - Sentence Length: {config['sentence_length']}
        - Maximum Total Words: {config['max_word_count']}
        - Appropriate Themes: {', '.join(config['themes'])}
        - Complexity Level: {config['complexity']}
        
        Characters:
        {json.dumps(characters, indent=2)}
        
        Story Structure Guidelines:
        """
        
        # Add audience-specific structure guidelines
        if audience in [AudienceType.TODDLERS, AudienceType.YOUNG_CHILDREN]:
            prompt += """
        - Simple, linear storyline
        - Clear cause and effect
        - Happy, reassuring ending
        - Repetitive elements for engagement
        - Focus on one main problem/solution
        """
        elif audience in [AudienceType.MIDDLE_GRADE, AudienceType.PRETEENS]:
            prompt += """
        - More complex plot with subplots
        - Character growth and development
        - Challenges that test characters
        - Meaningful resolution with lessons learned
        - Age-appropriate humor and tension
        """
        else:  # YA and Adults
            prompt += """
        - Complex, multi-layered narrative
        - Nuanced character development
        - Moral ambiguity allowed
        - Sophisticated themes and conflicts
        - Open or bittersweet endings acceptable
        """
        
        prompt += "\n\nCreate scenes that match this audience's reading level and interests."
        
        return prompt
    
    @staticmethod
    def adjust_content_for_audience(
        content: str,
        current_audience: AudienceType,
        target_audience: AudienceType
    ) -> str:
        """Create prompt to adjust existing content for different audience"""
        current_config = AudienceConfig.get_config(current_audience)
        target_config = AudienceConfig.get_config(target_audience)
        
        prompt = f"""
        Adapt the following story content from {current_audience.value} to {target_audience.value}:
        
        {content}
        
        Adjustments needed:
        - Change vocabulary from {current_config['vocabulary_level']} to {target_config['vocabulary_level']}
        - Adjust sentence length from {current_config['sentence_length']} to {target_config['sentence_length']}
        - Shift themes to include: {', '.join(target_config['themes'])}
        - Modify complexity from {current_config['complexity']} to {target_config['complexity']}
        
        Maintain the core story while making it appropriate for the new audience.
        """
        
        return prompt
```

### Step 10: Implement Audience Adjustment

#### 10.1 Add Audience Adjustment Endpoint
```python
# app/api/stories.py
# Add to existing file

@router.post("/{story_id}/adjust-audience", response_model=StoryResponse)
async def adjust_story_audience(
    story_id: str,
    target_audience: AudienceType,
    maintain_plot: bool = True,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Adjust story content for a different target audience"""
    try:
        return await StoryService.adjust_story_audience(
            story_id, target_audience, maintain_plot, user, db
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to adjust story audience: {str(e)}"
        )
```

## Week 5: Image Generation & Export

### Step 11: Scene-Based Image Generation

#### 11.1 Create Image Generation Service
```python
# app/services/image_service.py
import asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Story, StoryImage, User
from app.utils.openai_client import generate_image
import uuid
from datetime import datetime

class ImageGenerationService:
    
    @staticmethod
    async def generate_scene_images(
        story_id: str,
        user: User,
        db: AsyncSession,
        specific_scene_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate images for story scenes"""
        # Get story
        story = await StoryService.get_story_by_id(story_id, user, db)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        scenes = story.scenes or []
        if not scenes:
            raise HTTPException(status_code=400, detail="Story has no scenes")
        
        # Filter scenes if specific scene requested
        if specific_scene_id:
            scenes = [s for s in scenes if s['scene_id'] == specific_scene_id]
            if not scenes:
                raise HTTPException(status_code=404, detail="Scene not found")
        
        # Generate images for scenes
        generated_images = []
        for scene in scenes:
            # Skip if scene already has an image
            if scene.get('image_id'):
                continue
            
            try:
                # Generate image
                image_prompt = scene.get('image_prompt', '')
                if not image_prompt:
                    # Generate prompt if missing
                    image_prompt = await ImageGenerationService._generate_image_prompt(
                        scene, story
                    )
                
                # Call image generation
                image_b64 = await generate_image(image_prompt)
                
                # Store image
                image = StoryImage(
                    id=str(uuid.uuid4()),
                    story_id=story_id,
                    scene_id=scene['scene_id'],
                    image_type='scene',
                    base64_data=image_b64,
                    prompt=image_prompt,
                    created_at=datetime.now()
                )
                db.add(image)
                
                # Update scene with image ID
                scene['image_id'] = image.id
                
                generated_images.append({
                    'scene_id': scene['scene_id'],
                    'image_id': image.id,
                    'prompt': image_prompt
                })
                
                # Add small delay to avoid rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Failed to generate image for scene {scene['scene_id']}: {e}")
                continue
        
        # Update story with new scene data
        story.scenes = scenes
        await db.commit()
        
        return generated_images
    
    @staticmethod
    async def _generate_image_prompt(scene: Dict, story: Story) -> str:
        """Generate an image prompt for a scene"""
        audience_config = AudienceConfig.get_config(story.target_audience)
        
        style_guide = {
            AudienceType.TODDLERS: "simple, bright colors, cartoon style, friendly characters",
            AudienceType.YOUNG_CHILDREN: "colorful, whimsical, storybook illustration",
            AudienceType.MIDDLE_GRADE: "detailed illustration, adventure style, vibrant",
            AudienceType.PRETEENS: "semi-realistic, dynamic composition, emotional depth",
            AudienceType.YOUNG_ADULTS: "sophisticated illustration, atmospheric, mature themes",
            AudienceType.ADULTS: "artistic, nuanced, literary illustration style"
        }
        
        style = style_guide.get(story.target_audience, style_guide[AudienceType.MIDDLE_GRADE])
        
        prompt = f"{style}, {scene['title']}, {scene['content'][:150]}..."
        
        return prompt
```

#### 11.2 Add Image Generation Endpoints
```python
# app/api/stories.py
# Add to existing file

@router.post("/{story_id}/generate-scene-images")
async def generate_scene_images(
    story_id: str,
    scene_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Generate images for story scenes"""
    try:
        images = await ImageGenerationService.generate_scene_images(
            story_id, user, db, scene_id
        )
        return {"generated_images": images}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate images: {str(e)}"
        )

@router.get("/{story_id}/images")
async def get_story_images(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Get all images for a story"""
    try:
        return await ImageGenerationService.get_story_images(story_id, user, db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get images: {str(e)}"
        )
```

### Step 12: Export Functionality

#### 12.1 Create Export Service
```python
# app/services/export_service.py
import io
import base64
from typing import Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import markdown
from datetime import datetime

class ExportService:
    
    @staticmethod
    async def export_as_pdf(story: Story, include_images: bool = True) -> bytes:
        """Export story as PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story_elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2E86C1',
            spaceAfter=30
        )
        scene_title_style = ParagraphStyle(
            'SceneTitle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor='#5DADE2',
            spaceAfter=12
        )
        
        # Add title
        story_elements.append(Paragraph(story.title, title_style))
        story_elements.append(Spacer(1, 0.5*inch))
        
        # Add metadata
        metadata = f"Genre: {story.genre} | Audience: {story.target_audience} | Reading Time: {story.total_reading_time // 60} minutes"
        story_elements.append(Paragraph(metadata, styles['Italic']))
        story_elements.append(Spacer(1, 0.5*inch))
        
        # Add scenes
        for scene in story.scenes:
            # Scene title
            story_elements.append(Paragraph(scene['title'], scene_title_style))
            
            # Scene image (if available and requested)
            if include_images and scene.get('image_id'):
                # Fetch image from database
                image_data = await ExportService._get_image_data(scene['image_id'])
                if image_data:
                    img = Image(io.BytesIO(base64.b64decode(image_data)), width=4*inch, height=3*inch)
                    story_elements.append(img)
                    story_elements.append(Spacer(1, 0.2*inch))
            
            # Scene content
            for paragraph in scene['content'].split('\n\n'):
                if paragraph.strip():
                    story_elements.append(Paragraph(paragraph, styles['BodyText']))
                    story_elements.append(Spacer(1, 0.1*inch))
            
            # Page break after each scene (except last)
            if scene != story.scenes[-1]:
                story_elements.append(PageBreak())
        
        # Build PDF
        doc.build(story_elements)
        buffer.seek(0)
        return buffer.read()
    
    @staticmethod
    async def export_as_markdown(story: Story, include_image_links: bool = True) -> str:
        """Export story as Markdown"""
        md_content = f"# {story.title}\n\n"
        md_content += f"**Genre:** {story.genre} | **Audience:** {story.target_audience} | **Reading Time:** {story.total_reading_time // 60} minutes\n\n"
        md_content += "---\n\n"
        
        for i, scene in enumerate(story.scenes, 1):
            md_content += f"## Chapter {i}: {scene['title']}\n\n"
            
            if include_image_links and scene.get('image_id'):
                md_content += f"![Scene {i} Image](image_{scene['image_id']}.png)\n\n"
            
            md_content += f"{scene['content']}\n\n"
            md_content += "---\n\n"
        
        # Add lessons if available
        if story.content and 'lessons' in story.content:
            md_content += "## Lessons Learned\n\n"
            for lesson in story.content['lessons']:
                md_content += f"- {lesson}\n"
        
        return md_content
    
    @staticmethod
    async def export_as_epub(story: Story) -> bytes:
        """Export story as EPUB (placeholder - requires epub library)"""
        # This would require a library like ebooklib
        # For now, return markdown as bytes
        md_content = await ExportService.export_as_markdown(story)
        return md_content.encode('utf-8')
```

#### 12.2 Add Export Endpoints
```python
# app/api/stories.py
# Add to existing file

from fastapi.responses import Response

@router.get("/{story_id}/export/pdf")
async def export_story_as_pdf(
    story_id: str,
    include_images: bool = True,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Export story as PDF"""
    try:
        story = await StoryService.get_story_by_id(story_id, user, db)
        pdf_content = await ExportService.export_as_pdf(story, include_images)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=story_{story_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export PDF: {str(e)}"
        )

@router.get("/{story_id}/export/markdown")
async def export_story_as_markdown(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Export story as Markdown"""
    try:
        story = await StoryService.get_story_by_id(story_id, user, db)
        md_content = await ExportService.export_as_markdown(story)
        
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=story_{story_id}.md"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export Markdown: {str(e)}"
        )
```

## Testing Guidelines

### Unit Tests
```python
# tests/test_scene_parser.py
import pytest
from app.utils.scene_parser import SceneParser

def test_calculate_reading_time():
    text = "This is a test sentence with ten words in it."
    reading_time = SceneParser.calculate_reading_time(text)
    assert reading_time == 3  # 10 words at 200 wpm = 0.05 minutes = 3 seconds

def test_parse_story_structure():
    story_content = {
        "story_structure": {
            "introduction": "Once upon a time...",
            "middle": {
                "setting_out": "The heroes began their journey...",
                "tests": [
                    {"test_name": "First Challenge", "description": "They faced..."}
                ]
            },
            "climax": "At the peak of danger...",
            "conclusion": "And they lived happily..."
        }
    }
    
    scenes = SceneParser.parse_story_structure(story_content)
    assert len(scenes) == 5
    assert scenes[0].type == "introduction"
    assert scenes[-1].type == "conclusion"
```

### Integration Tests
```python
# tests/test_refinement_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_refine_scene(client: AsyncClient, auth_headers: dict):
    # Create story first
    story_response = await client.post(
        "/stories/",
        json={
            "title": "Test Story",
            "description": "A test story",
            "character_ids": ["char1", "char2"]
        },
        headers=auth_headers
    )
    story_id = story_response.json()["id"]
    
    # Generate content
    await client.post(f"/stories/{story_id}/content", headers=auth_headers)
    
    # Refine a scene
    refinement_response = await client.post(
        f"/stories/{story_id}/refine-scene/scene_1",
        json={
            "refinement_type": "simplify_language",
            "preserve_elements": ["main character names"]
        },
        headers=auth_headers
    )
    
    assert refinement_response.status_code == 200
    assert "refined_scene" in refinement_response.json()
```

## Success Criteria

### Week 1-2: Enhanced Story Structure ✓
- [ ] Database migration completed successfully
- [ ] Stories generate with scene-based structure
- [ ] Each scene has proper metadata (reading time, word count)
- [ ] API returns scenes in structured format
- [ ] Existing stories can be migrated to new structure

### Week 3: Iterative Refinement System ✓
- [ ] Scene-level refinement working
- [ ] Story-level refinement working
- [ ] Version history tracking implemented
- [ ] Refinement history stored and retrievable
- [ ] Can revert to previous versions

### Week 4: Multi-Audience Support ✓
- [ ] All audience types defined and configurable
- [ ] Stories generate appropriately for each audience
- [ ] Can adjust existing stories to new audiences
- [ ] Prompts adapt based on audience selection
- [ ] Content complexity matches audience level

### Week 5: Image Generation & Export ✓
- [ ] Images generate for each scene
- [ ] Image prompts are audience-appropriate
- [ ] PDF export includes text and images
- [ ] Markdown export working
- [ ] Export formats maintain story structure

## Deployment Checklist

1. **Database Migration**
   ```bash
   alembic upgrade head
   ```

2. **Environment Variables**
   - Ensure OPENAI_API_KEY is set
   - Verify DATABASE_URL is correct

3. **Dependencies**
   ```bash
   pip install reportlab markdown pillow
   ```

4. **API Documentation**
   - Update OpenAPI schemas
   - Document new endpoints
   - Add example requests/responses

5. **Monitoring**
   - Set up logging for refinement operations
   - Monitor image generation costs
   - Track API response times

## Next Steps

After completing Phase 1:
1. Gather feedback on API improvements
2. Optimize performance for scene generation
3. Plan Phase 2: Frontend Development
4. Consider caching strategies for images
5. Implement rate limiting for expensive operations

This completes the Phase 1 implementation guide. The backend is now ready to support a rich, interactive frontend experience.
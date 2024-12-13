from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.db import CharacterStatus, Story, Character, User, get_async_session
from app.users.user import active_user
from app.utils.openai_client import (
    generate_story_details_with_openai,
)

router = APIRouter()

from pydantic import BaseModel
from typing import List, Optional


class StoryBasicUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]


class StoryInput(BaseModel):
    title: str
    description: Optional[str]
    character_ids: List[str]


class StoryResponse(BaseModel):
    id: str
    title: str
    optimized_title: Optional[str]
    description: Optional[str]
    optimized_description: Optional[str]
    character_ids: List[str]
    content: Optional[str]
    status: str


@router.post("/", response_model=StoryResponse)
async def create_story(
    story: StoryInput,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Create a new story."""
    # Validate characters
    query = select(Character).where(
        Character.id.in_(story.character_ids),
        Character.user_id == user.id,
        Character.status.in_([CharacterStatus.generated, CharacterStatus.finalized]),
    )
    result = await db.execute(query)
    characters = result.scalars().all()

    if len(characters) != len(story.character_ids):
        raise HTTPException(status_code=400, detail="Invalid character IDs.")

    new_story = Story(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title=story.title,
        description=story.description,
        character_ids=story.character_ids,
        status="draft",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(new_story)
    await db.commit()
    await db.refresh(new_story)
    return new_story


@router.post("/{story_id}/refine", response_model=StoryResponse)
async def refine_story_details(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Refine story details using the LLM."""
    query = select(Story).where(
        Story.id == story_id,
        Story.user_id == user.id,
    )
    result = await db.execute(query)
    story = result.scalars().first()

    # Fetch characters
    query = select(Character).where(
        Character.id.in_(story.character_ids),
        Character.user_id == user.id,
        Character.status.in_([CharacterStatus.generated, CharacterStatus.finalized]),
    )
    result = await db.execute(query)
    characters = result.scalars().all()

    if len(characters) != len(story.character_ids):
        raise HTTPException(status_code=400, detail="Invalid character IDs.")

    # Prepare input for LLM

    # Call the LLM
    try:
        response = await generate_story_details_with_openai(story, characters)
        print(response)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error refining story details: {e}"
        )

    print(response["character_roles"])

    story.optimized_title = response["optimized_title"]
    story.optimized_description = response["optimized_description"]
    story.character_roles = response["character_roles"]
    story.updated_at = datetime.now()

    await db.commit()
    await db.refresh(story)

    return {
        "id": story.id,
        "title": story.title,
        "optimized_title": response["optimized_title"],
        "description": story.description,
        "optimized_description": response["optimized_description"],
        "character_ids": story.character_ids,
        # "character_roles": response["character_roles"],
        "content": None,
        "status": story.status.value,
    }


@router.put("/{story_id}/update", response_model=StoryResponse)
async def update_story_basic_details(
    story_id: str,
    story_update: StoryBasicUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Update the title and description of a story."""
    # Fetch the story
    query = select(Story).where(
        Story.id == story_id,
        Story.user_id == user.id,
    )
    result = await db.execute(query)
    story = result.scalars().first()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found.")

    # Update fields if they are provided
    if story_update.title:
        story.title = story_update.title
    if story_update.description:
        story.description = story_update.description

    story.updated_at = datetime.now()

    # Commit the changes
    await db.commit()
    await db.refresh(story)

    return {
        "id": story.id,
        "title": story.title,
        "refined_title": story.refined_title,
        "description": story.description,
        "refined_description": story.refined_description,
        "character_ids": story.character_ids,
        "character_roles": story.character_roles,
        "content": story.content,
        "status": story.status,
    }

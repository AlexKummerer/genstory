from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.db import CharacterStatus, Story, Character, User, get_async_session
from app.users.user import active_user
from app.utils.openai_client import (
    generate_story_content,
    generate_story_details_with_openai,
)

router = APIRouter()

from pydantic import BaseModel, field_validator
from typing import List, Optional


class StoryBasicUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]

    @field_validator("description")
    def validate_description(cls, v):
        if len(v) < 20:
            raise ValueError("Description should be at least 10 characters.")
        return v

    @field_validator("title")
    def validate_title(cls, v):
        if len(v) < 5:
            raise ValueError("Title should be at least 10 characters.")
        return v


class StoryInput(BaseModel):
    title: str
    description: Optional[str]
    character_ids: List[str]

    @field_validator("character_ids")
    def validate_character_ids(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 characters are required.")
        return v

    @field_validator("description")
    def validate_description(cls, v):
        if len(v) < 20:
            raise ValueError("Description should be at least 10 characters.")
        return v

    @field_validator("title")
    def validate_title(cls, v):
        if len(v) < 5:
            raise ValueError("Title should be at least 10 characters.")
        return v


class StoryResponse(BaseModel):
    id: str
    title: str
    optimized_title: Optional[str]
    description: Optional[str]
    optimized_description: Optional[str]
    character_ids: List[str]
    character_roles: Optional[List[dict]]
    content: Optional[List[str]]
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

    print(characters)

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
        "character_roles": response["character_roles"],
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
        story.optimized_title = None
    if story_update.description:
        story.description = story_update.description
        story.optimized_description = None

    story.updated_at = datetime.now()

    # Commit the changes
    await db.commit()
    await db.refresh(story)

    return {
        "id": story.id,
        "title": story.title,
        "optimized_title": story.optimized_title,
        "description": story.description,
        "optimized_description": story.optimized_description,
        "character_ids": story.character_ids,
        "character_roles": story.character_roles,
        "content": None,
        "status": story.status.value,
    }


@router.get("/", response_model=List[StoryResponse])
async def get_stories(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Get all stories for the authenticated user."""
    query = select(Story).where(Story.user_id == user.id)
    result = await db.execute(query)
    stories = result.scalars().all()

    return stories


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Get a story by ID."""
    query = select(Story).where(
        Story.id == story_id,
        Story.user_id == user.id,
    )
    result = await db.execute(query)
    story = result.scalars().first()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found.")

    return story


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Delete a story by ID."""
    query = select(Story).where(
        Story.id == story_id,
        Story.user_id == user.id,
    )
    result = await db.execute(query)
    story = result.scalars().first()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found.")

    db.delete(story)
    await db.commit()

    return {"message": "Story deleted successfully."}


@router.post("/{story_id}/content", response_model=StoryResponse)
async def create_story_content(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Update the content of a story."""
    # Fetch the story
    query = select(Story).where(
        Story.id == story_id,
        Story.user_id == user.id,
    )
    result = await db.execute(query)
    story = result.scalars().first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found.")

    content = await generate_story_content(story)
    # Update the content
    story.content = content
    story.updated_at = datetime.now()
    # Commit the changes
    await db.commit()
    await db.refresh(story)
    return {
        "id": story.id,
        "title": story.title,
        "optimized_title": story.optimized_title,
        "description": story.description,
        "optimized_description": story.optimized_description,
        "character_ids": story.character_ids,
        "character_roles": story.character_roles,
        "content": story.content,
        "status": story.status.value,
    }

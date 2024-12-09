from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.db import Story, Character, User, get_async_session
from app.schemas.schemas import StoryInput, StoryResponse
from app.users.user import active_user
from app.utils.openai_client import (
    generate_story_details_with_openai,
    generate_story_with_openai,
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
    description: Optional[str]
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


@router.post("/{story_id}/generate", response_model=StoryResponse)
async def generate_story(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Generate story content based on characters and description."""
    query = select(Story).where(
        Story.id == story_id,
        Story.user_id == user.id,
    )
    result = await db.execute(query)
    story = result.scalars().first()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found.")

    # Fetch associated characters
    character_query = select(Character).where(
        Character.id.in_(story.character_ids),
        Character.user_id == user.id,
    )
    character_result = await db.execute(character_query)
    characters = character_result.scalars().all()

    # Generate the story using characters and description
    try:
        story_content = "This is a test story content."
        story_content = await generate_story_with_openai(
            story.title, story.description, characters
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating story: {e}")

    story.content = story_content
    story.status = "draft"
    story.updated_at = datetime.now()

    await db.commit()
    await db.refresh(story)
    return story


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Fetch a specific story and its characters."""
    story_query = select(Story).where(
        Story.id == story_id,
        Story.user_id == user.id,
    )
    story_result = await db.execute(story_query)
    story = story_result.scalars().first()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found.")

    # Fetch associated characters
    character_query = select(Character).where(
        Character.id.in_(story.character_ids),
        Character.user_id == user.id,
    )
    character_result = await db.execute(character_query)
    characters = character_result.scalars().all()

    return {
        "id": story.id,
        "title": story.title,
        "description": story.description,
        "character_ids": story.character_ids,
        "content": story.content,
        "status": story.status,
        "characters": [
            {
                "id": c.id,
                "name": c.character_name,
                "description": c.character_description,
                "traits": c.character_traits,
                "story_context": c.character_story_context,
            }
            for c in characters
        ],
    }


@router.post("/refine", response_model=StoryResponse)
async def refine_story_details(
    story: StoryInput,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Refine story details using the LLM."""
    # Fetch characters
    query = select(Character).where(
        Character.id.in_(story.character_ids),
        Character.user_id == user.id,
    )
    result = await db.execute(query)
    characters = result.scalars().all()

    if len(characters) != len(story.character_ids):
        raise HTTPException(status_code=400, detail="Invalid character IDs.")

    # Prepare input for LLM

    # Call the LLM
    try:
        response = await generate_story_details_with_openai(story, characters)
        refined_details = response["choices"][0]["text"].strip()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error refining story details: {e}"
        )

    # Parse the LLM output (custom logic based on LLM response format)
    # Example: parse the response to extract title, description, and roles
    refined_title = refined_details.split("Title:")[1].split("\n")[0].strip()
    refined_description = (
        refined_details.split("Description:")[1].split("\n")[0].strip()
    )
    character_roles = refined_details.split("Roles:")[1].strip()

    return {
        "title": refined_title,
        "description": refined_description,
        "character_ids": story.character_ids,
        "content": None,
        "status": "draft",
        "roles": character_roles,  # Include character roles as part of the response
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


@router.delete("/{story_id}", response_model=dict)
async def delete_story(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Delete a story by ID."""
    # Fetch the story to ensure it exists and belongs to the user
    query = select(Story).where(
        Story.id == story_id,
        Story.user_id == user.id,
    )
    result = await db.execute(query)
    story = result.scalars().first()

    if not story:
        raise HTTPException(status_code=404, detail="Story not found.")

    # Delete the story
    await db.delete(story)
    await db.commit()

    return {"message": f"Story with ID {story_id} deleted successfully."}

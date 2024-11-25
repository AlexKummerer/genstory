from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Optional
from app.db.db import Character, CharacterStatus, User
from app.db.db import get_async_session
from app.users.user import active_user

router = APIRouter()


# Pydantic Models
class CharacterInput(BaseModel):
    description: str = Field(..., title="Description", max_length=500)
    name: str | None = Field(None, title="Name", max_length=100)


class CharacterUpdateInput(BaseModel):
    description: str | None = None
    name: str | None = None
    generated_traits: dict | None = None
    story_context: str | None = None


class CharacterResponse(BaseModel):
    id: str
    name: str | None
    description: str
    generated_traits: dict | None
    story_context: str | None
    generated_summary: str | None
    status: str


class CharacterListResponse(BaseModel):
    id: str
    name: str | None
    description: str
    status: str


# Mock LLM Function for Generating Data
def mock_llm_generate(description: str):
    return {
        "generated_traits": {"brave": True, "intelligent": True},
        "story_context": f"This is a context generated based on: {description}",
        "generated_summary": f"This is a summary generated for: {description}",
    }


# Routes


@router.post("/", response_model=CharacterResponse)
async def create_character(
    data: CharacterInput,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Create a new character with draft status."""

    new_character = Character(
        id=str(uuid4()),
        user_description=data.description,
        name=data.name,
        user_id=user.id,
        status=CharacterStatus.draft,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    print(new_character)
    db.add(new_character)
    await db.commit()
    await db.refresh(new_character)

    return {
        "id": new_character.id,
        "name": new_character.name,
        "description": new_character.user_description,
        "generated_traits": new_character.generated_traits,
        "story_context": new_character.story_context,
        "generated_summary": new_character.generated_summary,
        "status": new_character.status.value,
    }


@router.post("/{character_id}/generate", response_model=CharacterResponse)
async def generate_character(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Generate traits, context, and summary for a draft character."""
    query = (
        select(Character)
        .where(Character.user_id == user.id)
        .where(Character.id == character_id)
    )
    result = await db.execute(query)
    character = result.scalars().first()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.status not in {CharacterStatus.draft, CharacterStatus.generated}:
        raise HTTPException(
            status_code=400, detail="Character must be in draft or generated status."
        )

    generated_data = mock_llm_generate(character.user_description)
    character.generated_traits = generated_data["generated_traits"]
    character.story_context = generated_data["story_context"]
    character.generated_summary = generated_data["generated_summary"]
    character.status = CharacterStatus.generated
    character.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(character)

    return {
        "id": character.id,
        "name": character.name,
        "description": character.user_description,
        "generated_traits": character.generated_traits,
        "story_context": character.story_context,
        "generated_summary": character.generated_summary,
        "status": character.status.value,
    }


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    data: CharacterUpdateInput,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Update name, description, traits, or context for a character."""
    query = (
        select(Character)
        .where(Character.user_id == user.id)
        .where(Character.id == character_id)
    )
    result = await db.execute(query)
    character = result.scalars().first()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.status == CharacterStatus.finalized:
        raise HTTPException(
            status_code=400, detail="Finalized characters cannot be modified."
        )

    if data.description is not None:
        character.user_description = data.description
    if data.name is not None:
        character.name = data.name
    if data.generated_traits is not None:
        character.generated_traits = data.generated_traits
    if data.story_context is not None:
        character.story_context = data.story_context

    character.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(character)

    return {
        "id": character.id,
        "name": character.name,
        "description": character.user_description,
        "generated_traits": character.generated_traits,
        "story_context": character.story_context,
        "generated_summary": character.generated_summary,
        "status": character.status.value,
    }


@router.post("/{character_id}/finalize", response_model=CharacterResponse)
async def finalize_character(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Finalize a character, preventing further modifications."""
    query = (
        select(Character)
        .where(Character.user_id == user.id)
        .where(Character.id == character_id)
    )
    result = await db.execute(query)
    character = result.scalars().first()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.status != CharacterStatus.generated:
        raise HTTPException(
            status_code=400, detail="Only generated characters can be finalized."
        )

    character.status = CharacterStatus.finalized
    character.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(character)

    return {
        "id": character.id,
        "name": character.name,
        "description": character.user_description,
        "generated_traits": character.generated_traits,
        "story_context": character.story_context,
        "generated_summary": character.generated_summary,
        "status": character.status.value,
    }


@router.get("/", response_model=List[CharacterListResponse])
async def get_all_characters(
    status: Optional[CharacterStatus] = Query(None),
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Fetch all characters, optionally filtered by status."""
    query = select(Character).where(Character.user_id == user.id)
    if status:
        query = query.where(Character.status == status)

    result = await db.execute(query)
    characters = result.scalars().all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.user_description,
            "status": c.status.value,
        }
        for c in characters
    ]


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Fetch a specific character by ID."""
    query = (
        select(Character)
        .where(Character.user_id == user.id)
        .where(Character.id == character_id)
    )
    result = await db.execute(query)
    character = result.scalars().first()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    return {
        "id": character.id,
        "name": character.name,
        "description": character.user_description,
        "generated_traits": character.generated_traits,
        "story_context": character.story_context,
        "generated_summary": character.generated_summary,
        "status": character.status.value,
    }

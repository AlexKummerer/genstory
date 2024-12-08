from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, List, Optional
from app.db.db import Character, CharacterStatus, User
from app.db.db import get_async_session
from app.users.user import active_user

from app.utils.openai_client import generate_character_with_openai

router = APIRouter()


# Pydantic Models
class CharacterInput(BaseModel):
    description: str = Field(..., title="Description", max_length=1000)
    name: str | None = Field(None, title="Name", max_length=100)
    traits: dict | None = Field(
        {
            "curious": "Updated description emphasizing exploration and its impact on the plot.",
            "brave": "Enhanced description focusing on how bravery shapes key moments.",
            "sympathetic": "Deepened description of empathy that connects with readers.",
            "cunning": "Expanded narrative on cunning, showing complex tactical acumen.",
            "resolute": "Strengthened portrayal of determination and its role in overcoming challenges.",
        },
        title="Traits",
    )
    story_context: str | None = Field(None, title="Story Context")

    def __repr__(self):
        return f"{self.description} {self.name} {self.traits} {self.story_context}"


class CharacterResponse(BaseModel):
    id: str
    chat_id: str | None
    character_name: str | None
    optimized_name: str | None
    character_description: str
    optimized_description: str | None
    character_traits: dict | None
    optimized_traits: dict | None
    character_story_context: str | None
    optimized_story_context: str | None
    status: str

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return super().__call__(*args, **kwds)


class CharacterListResponse(BaseModel):
    id: str
    chat_id: str | None
    character_name: str | None
    optimized_name: str | None
    character_description: str
    optimized_description: str | None
    character_traits: dict | None
    optimized_traits: dict | None
    character_story_context: str | None
    optimized_story_context: str | None
    status: str

    def __repr__(self):
        return f"{self.id} {self.character_name} {self.character_description} {self.status}"


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
    print(data)
    new_character = Character(
        id=str(uuid4()),
        character_name=data.name,
        character_description=data.description,
        character_traits=data.traits,
        character_story_context=data.story_context,
        user_id=user.id,
        status=CharacterStatus.draft,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    print(new_character)
    try:
        db.add(new_character)
        await db.commit()
        await db.refresh(new_character)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error creating character")

    return {
        "id": new_character.id,
        "character_name": new_character.character_name,
        "optimized_name": new_character.optimized_name,
        "chat_id": new_character.chat_id,
        "character_description": new_character.character_description,
        "optimized_description": new_character.optimized_description,
        "character_traits": new_character.character_traits,
        "optimized_traits": new_character.character_traits,
        "character_story_context": new_character.character_story_context,
        "optimized_story_context": new_character.optimized_story_context,
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
    
    print(query, "query")
    generated_data = None
    result = await db.execute(query)
    character = result.scalars().first()
    print(character, "character")
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.status not in {CharacterStatus.draft, CharacterStatus.generated}:
        raise HTTPException(
            status_code=400, detail="Character must be in draft or generated status."
        )

    try:
        generated_data, chat_id = await generate_character_with_openai(character)
        print(generated_data, chat_id, "generated_data")

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    character.optimized_name = generated_data["optimized_name"]
    character.optimized_description = generated_data["optimized_description"]
    character.chat_id = chat_id
    character.optimized_traits = generated_data["optimized_traits"]
    character.optimized_story_context = generated_data["optimized_story_context"]
    character.status = CharacterStatus.generated.value
    character.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(character)

    return {
        "id": character.id,
        "chat_id": character.chat_id,
        "character_name": character.character_name,
        "optimized_name": character.optimized_name,
        "character_description": character.character_description,
        "optimized_description": character.optimized_description,  #
        "character_traits": character.character_traits,
        "optimized_traits": character.optimized_traits,
        "character_story_context": character.character_story_context,
        "optimized_story_context": character.optimized_story_context,
        "generated_summary": character.generated_summary,
        "status": character.status,
    }


@router.put("/{character_id}/save", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    data: CharacterInput,
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
    print(data, "data")

    character.character_name = data.name
    character.optimized_name = None
    character.character_description = data.description
    character.optimized_description = None
    character.character_traits = data.traits
    character.optimized_traits = None
    character.character_story_context = data.story_context
    character.optimized_story_context = None
    character.status = CharacterStatus.generated.value
    character.updated_at = datetime.now(timezone.utc)

    character.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(character)

    return {
        "id": character.id,
        "chat_id": character.chat_id,
        "character_name": character.character_name,
        "optimized_name": character.optimized_name,
        "character_description": character.character_description,
        "optimized_description": character.optimized_description,
        "character_traits": character.character_traits,
        "optimized_traits": character.optimized_traits,
        "character_story_context": character.character_story_context,
        "optimized_story_context": character.optimized_story_context,
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
        "chat_id": character.chat_id,
        "character_name": character.character_name,
        "optimized_name": character.optimized_name,
        "character_description": character.character_description,
        "optimized_description": character.optimized_description,
        "character_traits": character.character_traits,
        "optimized_traits": character.optimized_traits,
        "character_story_context": character.character_story_context,
        "optimized_story_context": character.optimized_story_context,
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
            "character_name": c.character_name,
            "optimized_name": c.optimized_name,
            "chat_id": c.chat_id,
            "character_description": c.character_description,
            "optimized_description": c.optimized_description,
            "character_traits": c.character_traits,
            "optimized_traits": c.optimized_traits,
            "character_story_context": c.character_story_context,
            "optimized_story_context": c.optimized_story_context,
            "generated_summary": c.generated_summary,
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
        "chat_id": character.chat_id,
        "character_name": character.character_name,
        "optimized_name": character.optimized_name,
        "character_description": character.character_description,
        "optimized_description": character.optimized_description,
        "character_traits": character.character_traits,
        "optimized_traits": character.optimized_traits,
        "character_story_context": character.character_story_context,
        "optimized_story_context": character.optimized_story_context,
        "generated_summary": character.generated_summary,
        "status": character.status.value,
    }


@router.delete("/{character_id}")
async def delete_character(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Delete a character by ID."""
    query = (
        select(Character)
        .where(Character.user_id == user.id)
        .where(Character.id == character_id)
    )
    result = await db.execute(query)
    character = result.scalars().first()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    db.delete(character)
    await db.commit()

    return {"message": "Character deleted successfully."}

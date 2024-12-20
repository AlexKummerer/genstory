import json
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.db.models import Character, CharacterStatus, User
from app.db.db import get_async_session
from app.services.character_service import CharacterService
from app.schemas.characters import CharacterInput, CharacterResponse
from app.users.user import active_user, fastapi_users

router = APIRouter()


@router.post("/", response_model=CharacterResponse)
async def create_character(
    data: CharacterInput,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(fastapi_users.current_user(active=True)),
):
    """Create a new character with draft status."""
    try:
        print("data", data)
        return await CharacterService.create_character(data, db, user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{character_id}/generate", response_model=CharacterResponse)
async def generate_character(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Generate traits, context, and summary for a draft character."""
    try:
        return await CharacterService.generate_character(character_id, db, user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.put("/{character_id}/save", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    data: CharacterInput,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Update name, description, traits, or context for a character."""
    try:
        return await CharacterService.update_character(character_id, data, db, user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{character_id}/finalize", response_model=CharacterResponse)
async def finalize_character(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Finalize a character, preventing further modifications."""
    try:
        return await CharacterService.finalize_character(character_id, db, user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/", response_model=List[CharacterResponse])
async def get_all_characters(
    status: Optional[CharacterStatus] = Query(None),
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Fetch all characters, optionally filtered by status."""
    try:
        return await CharacterService.get_all_characters(status, page, size, db, user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{character_id}", response_model=CharacterResponse)
async def fetch_character_by_id(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Fetch a specific character by ID."""
    try:
        return await CharacterService.get_character_by_id(character_id, db, user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{character_id}")
async def delete_character(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Delete a character by ID."""
    try:
        return await CharacterService.delete_character(character_id, db, user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

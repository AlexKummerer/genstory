from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.models import CharacterStatus, Story, Character, StoryStatus, User
from app.db.db import get_async_session
from app.schemas.stories import (
    ImageDownloadResponse,
    ImageResponse,
    StoryBasicUpdate,
    StoryInput,
    StoryResponse,
)
from app.services.story_service import StoryService
from app.users.user import active_user
from app.utils.openai_client import (
    EnhancedStory,
    FullStoryDetails,
    generate_story_content,
    generate_story_details_with_openai,
)

router = APIRouter()

from pydantic import BaseModel, field_validator
from typing import List, Optional


@router.post("/", response_model=StoryResponse)
async def create_story(
    story: StoryInput,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Create a new story."""
    try:
        return await StoryService.create_story(story, user, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create story: {str(e)}")


@router.get("/", response_model=List[StoryResponse])
async def get_stories(
    status: Optional[StoryStatus] = Query(None),
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Get all stories for the authenticated user."""

    try:

        return await StoryService.get_all_stories(
            status,
            page,
            size,
            user,
            db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stories: {str(e)}")


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):

    try:
        return await StoryService.get_story_by_id(story_id, user, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get story: {str(e)}")


@router.post("/{story_id}/refine", response_model=StoryResponse)
async def refine_story_details(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    try:
        return await StoryService.refine_story_details(story_id, user, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refine story: {str(e)}")


@router.put("/{story_id}/update", response_model=StoryResponse)
async def update_story_basic_details(
    story_id: str,
    story_update: StoryBasicUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Update the title and description of a story."""

    try:
        return await StoryService.update_story(story_id, story_update, user, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update story: {str(e)}")


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    try:
        return await StoryService.delete_story(story_id, user, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete story: {str(e)}")


@router.post("/{story_id}/content", response_model=StoryResponse)
async def create_story_content(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Update the content of a story."""
    try:
        return await StoryService.create_story_content(story_id, user, db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create story content: {str(e)}"
        )


@router.post("/{story_id}/cover_image", response_model=ImageResponse)
async def create_story_cover_image(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Update the cover image of a story."""
    try:
        return await StoryService.create_story_cover_image(story_id, user, db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create story cover image: {str(e)}"
        )


@router.get("{story_id}/cover_image/", response_model=ImageResponse)
async def get_cover_image(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Get the cover image of a story."""
    try:
        return await StoryService.get_cover_image(story_id, user, db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get story cover image: {str(e)}"
        )


@router.post("/{story_id}/download_cover_image", response_model=ImageDownloadResponse)
async def download_cover_image(
    story_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(active_user),
):
    """Download the cover image of a story."""
    try:
        return await StoryService.download_cover_image(
            story_id, user, db, download_route="downloads/story_covers"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download story cover image: {str(e)}"
        )

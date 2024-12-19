from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import Story, User
from fastapi import HTTPException
from uuid import uuid4
from datetime import datetime, timezone

class StoryService:
    @staticmethod
    async def create_story(title: str, description: str, user: User, db: AsyncSession):
        """Create a new story."""
        new_story = Story(
            id=str(uuid4()),
            user_id=user.id,
            title=title,
            description=description,
            status="draft",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_story)
        await db.commit()
        await db.refresh(new_story)
        return new_story

    @staticmethod
    async def get_story_by_id(story_id: str, user: User, db: AsyncSession):
        """Fetch a story by its ID."""
        query = select(Story).where(Story.id == story_id, Story.user_id == user.id)
        result = await db.execute(query)
        story = result.scalars().first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        return story

    @staticmethod
    async def update_story(story_id: str, title: str, description: str, user: User, db: AsyncSession):
        """Update an existing story."""
        story = await StoryService.get_story_by_id(story_id, user, db)
        story.title = title
        story.description = description
        story.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(story)
        return story

    @staticmethod
    async def delete_story(story_id: str, user: User, db: AsyncSession):
        """Delete a story by its ID."""
        story = await StoryService.get_story_by_id(story_id, user, db)
        await db.delete(story)
        await db.commit()
        return {"message": "Story deleted successfully."}
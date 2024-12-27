import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import Character, CharacterStatus, Story, StoryStatus, User
from fastapi import HTTPException
from uuid import uuid4
from datetime import datetime, timezone

from app.schemas.stories import StoryBasicUpdate, StoryInput
from app.utils.openai_client import (
    FullStoryDetails,
    generate_story_content,
    generate_story_details_with_openai,
)


class StoryService:
    @staticmethod
    async def create_story(story: StoryInput, user: User, db: AsyncSession):
        """Create a new story."""
        query = select(Character).where(
            Character.id.in_(story.character_ids),
            Character.user_id == user.id,
            Character.status.in_(
                [CharacterStatus.generated, CharacterStatus.finalized]
            ),
        )

        result = await db.execute(query)
        characters = result.scalars().all()

        if len(characters) != len(story.character_ids):
            raise HTTPException(status_code=400, detail="Invalid character IDs.")

        print(characters)
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
        return new_story.to_response()

    @staticmethod
    async def get_all_stories(
        status: StoryStatus, page: int, size: int, user: User, db: AsyncSession
    ):
        """Fetch all stories created by a user."""
        """Fetch all characters for a user, optionally filtered by status."""
        try:
            offset = (page - 1) * size
            query = (
                select(Story).where(Story.user_id == user.id).offset(offset).limit(size)
            )

            if status:
                query = query.where(Story.status == status)

            result = await db.execute(query)
            stories = result.scalars().all()
            return [story.to_response() for story in stories]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch characters: {str(e)}",
            )

    @staticmethod
    async def get_story_by_id(story_id: str, user: User, db: AsyncSession):
        """Fetch a story by its ID."""
        query = select(Story).where(Story.id == story_id, Story.user_id == user.id)
        result = await db.execute(query)
        story = result.scalars().first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        return story.to_response()

    @staticmethod
    async def refine_story_details(story_id: str, user: User, db: AsyncSession):
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
            Character.status.in_(
                [CharacterStatus.generated, CharacterStatus.finalized]
            ),
        )
        result = await db.execute(query)
        characters = result.scalars().all()

        print(characters)

        if len(characters) != len(story.character_ids):
            raise HTTPException(status_code=400, detail="Invalid character IDs.")

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
        story.status = "generated"
        story.updated_at = datetime.now()

        await db.commit()
        await db.refresh(story)
        return story.to_response()

    @staticmethod
    async def update_story(
        story_id: str, story_update: StoryBasicUpdate, user: User, db: AsyncSession
    ):
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

        return story.to_response()

    @staticmethod
    async def delete_story(story_id: str, user: User, db: AsyncSession):
        """Delete a story by its ID."""
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

    @staticmethod
    async def create_story_content(story_id: str, user: User, db: AsyncSession):

        # Fetch the story
        query = select(Story).where(
            Story.id == story_id,
            Story.user_id == user.id,
        )
        result = await db.execute(query)
        story = result.scalars().first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found.")

        content: FullStoryDetails = await generate_story_content(story)
        # Update the content
        story.content = content
        story.status = "finalized"
        story.updated_at = datetime.now()
        # Commit the changes
        await db.commit()
        await db.refresh(story)
        return story.to_response()
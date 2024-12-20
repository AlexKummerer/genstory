from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from uuid import uuid4
from app.db.models import Character, CharacterStatus, User
from app.schemas.characters import CharacterInput
from app.utils.openai_client import generate_character_with_openai


class CharacterService:
    @staticmethod
    async def create_character(data: CharacterInput, db: AsyncSession, user: User):
        """Create a new character with draft status."""
        try:

            traits = (
                [trait.model_dump() for trait in data.traits] if data.traits else None
            )

            print("traits", traits)

            new_character = Character(
                id=str(uuid4()),
                character_name=data.name,
                character_description=data.description,
                character_traits=traits,
                user_id=user.id,
                status=CharacterStatus.draft,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(new_character)
            await db.commit()
            await db.refresh(new_character)
            print("new_character", new_character.to_response())
            return new_character.to_response()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create character: {str(e)}",
            )

    @staticmethod
    async def generate_character(character_id: str, db: AsyncSession, user: User):
        """Generate traits, context, and summary for a draft character."""
        try:
            query = select(Character).where(
                Character.id == character_id, Character.user_id == user.id
            )
            result = await db.execute(query)
            character = result.scalars().first()

            if not character:
                raise HTTPException(status_code=404, detail="Character not found")
            if character.status not in {
                CharacterStatus.draft,
                CharacterStatus.generated,
            }:
                raise HTTPException(
                    status_code=400,
                    detail="Character must be in draft or generated status.",
                )

            generated_data = await generate_character_with_openai(character)

            character.optimized_name = generated_data["optimized_name"]
            character.optimized_description = generated_data["optimized_description"]
            character.optimized_traits = generated_data["optimized_traits"]
            character.optimized_story_context = generated_data[
                "optimized_story_context"
            ]
            character.status = CharacterStatus.generated
            character.updated_at = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(character)
            return character.to_response()
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate character: {str(e)}",
            )

    @staticmethod
    async def update_character(
        character_id: str, data: CharacterInput, db: AsyncSession, user: User
    ):
        """Update character details."""
        try:
            query = select(Character).where(
                Character.id == character_id, Character.user_id == user.id
            )
            result = await db.execute(query)
            character = result.scalars().first()

            if not character:
                raise HTTPException(status_code=404, detail="Character not found")
            if character.status == CharacterStatus.finalized:
                raise HTTPException(
                    status_code=400, detail="Finalized characters cannot be modified."
                )

            character.character_name = data.name
            character.optimized_name = None
            character.character_description = data.description
            character.optimized_description = None
            character.character_traits = (
                [trait.model_dump() for trait in data.traits] if data.traits else None
            )
            character.optimized_traits = None
            character.status = CharacterStatus.generated
            character.updated_at = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(character)
            return character.to_response()
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update character: {str(e)}",
            )

    @staticmethod
    async def finalize_character(character_id: str, db: AsyncSession, user: User):
        """Finalize a character to prevent further modifications."""
        try:
            query = select(Character).where(
                Character.id == character_id, Character.user_id == user.id
            )
            result = await db.execute(query)
            character = result.scalars().first()

            if not character:
                raise HTTPException(status_code=404, detail="Character not found")
            if character.status != CharacterStatus.generated:
                raise HTTPException(
                    status_code=400,
                    detail="Only generated characters can be finalized.",
                )

            character.status = CharacterStatus.finalized
            character.updated_at = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(character)
            return character.to_response()
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to finalize character: {str(e)}",
            )

    @staticmethod
    async def get_all_characters(
        status: CharacterStatus, page: int, size: int, db: AsyncSession, user: User
    ):
        """Fetch all characters for a user, optionally filtered by status."""
        try:
            offset = (page - 1) * size
            query = (
                select(Character)
                .where(Character.user_id == user.id)
                .offset(offset)
                .limit(size)
            )

            if status:
                query = query.where(Character.status == status)

            result = await db.execute(query)
            characters = result.scalars().all()
            return [character.to_response() for character in characters]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch characters: {str(e)}",
            )

    @staticmethod
    async def get_character_by_id(character_id: str, db: AsyncSession, user: User):
        """Fetch a character by ID."""
        try:
            query = select(Character).where(
                Character.id == character_id, Character.user_id == user.id
            )
            result = await db.execute(query)
            character = result.scalars().first()

            if not character:
                raise HTTPException(status_code=404, detail="Character not found")

            return character.to_response()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch character: {str(e)}",
            )

    @staticmethod
    async def delete_character(character_id: str, db: AsyncSession, user: User):
        """Delete a character by ID."""
        try:
            query = select(Character).where(
                Character.id == character_id, Character.user_id == user.id
            )
            result = await db.execute(query)
            character = result.scalars().first()

            if not character:
                raise HTTPException(status_code=404, detail="Character not found")

            await db.delete(character)
            await db.commit()

            return {"message": "Character deleted successfully."}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete character: {str(e)}",
            )

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import User
from fastapi import HTTPException
from uuid import uuid4


class UserService:
    @staticmethod
    async def get_user_by_id(user_id: str, db: AsyncSession):
        """Fetch a user by their ID."""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    async def create_user(
        username: str, email: str, hashed_password: str, db: AsyncSession
    ):
        """Create a new user."""
        new_user = User(
            id=str(uuid4()),
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def update_user(user_id: str, username: str, email: str, db: AsyncSession):
        """Update user details."""
        user = await UserService.get_user_by_id(user_id, db)
        user.username = username
        user.email = email
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(user_id: str, db: AsyncSession):
        """Delete a user by their ID."""
        user = await UserService.get_user_by_id(user_id, db)
        await db.delete(user)
        await db.commit()
        return {"message": "User deleted successfully."}

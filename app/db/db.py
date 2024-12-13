from dataclasses import Field
import enum
import os
import uuid
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    String,
    Text,
    JSON,
    TIMESTAMP,
    ForeignKey,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(BASE_DIR)
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR,'test.db')}"
print(DATABASE_URL)

Base = declarative_base()


class CharacterStatus(str, enum.Enum):
    draft = "draft"
    generated = "generated"
    finalized = "finalized"


class StoryStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"
    updated = "updated"


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    username = Column(String(20), unique=False, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    characters = relationship("Character", back_populates="user")
    stories = relationship("Story", back_populates="user")


class Character(Base):
    __tablename__ = "characters"

    id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )  # UUID as String
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    chat_id = Column(String, nullable=True)
    character_description = Column(Text, nullable=True)
    optimized_description = Column(Text, nullable=True)
    character_name = Column(String(100), nullable=True)
    optimized_name = Column(String(100), nullable=True)
    character_traits = Column(JSON, nullable=True)
    optimized_traits = Column(JSON, nullable=True)
    character_story_context = Column(Text, nullable=True)
    optimized_story_context = Column(Text, nullable=True)
    generated_summary = Column(Text, nullable=True)
    status = Column(SQLAlchemyEnum(CharacterStatus), nullable=True)  # or use StatusEnum
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)

    # Relationships
    user = relationship("User", back_populates="characters")

    def __repr__(self):
        return f"Character(id={self.id!r}, user_id={self.user_id!r}, user_description={self.character_description!r}, name={self.character_name!r}, generated_traits={self.character_traits!r}, story_context={self.character_story_context!r}, generated_summary={self.generated_summary!r}, status={self.status!r}, created_at={self.created_at!r}, updated_at={self.updated_at!r})"


class Story(Base):
    __tablename__ = "stories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    optimized_title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    optimized_description = Column(Text, nullable=True)
    character_ids = Column(JSON, nullable=True)  # Store related character IDs
    character_roles = Column(JSON, nullable=True)  # Stores roles for each character
    content = Column(Text, nullable=True)
    status = Column(
        SQLAlchemyEnum(StoryStatus), nullable=False, default=StoryStatus.draft
    )
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)

    # Relationships
    user = relationship("User", back_populates="stories")


engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session():
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session=session, user_table=User)

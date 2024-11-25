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
    username = Column(String(20), unique=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    characters = relationship("Character", back_populates="user")
    stories = relationship("Story", back_populates="user")


class Character(Base):
    __tablename__ = "characters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID as String
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_description = Column(Text, nullable=False)

    name = Column(String(100), nullable=True)
    generated_traits = Column(JSON, nullable=True)
    story_context = Column(Text, nullable=True)
    generated_summary = Column(Text, nullable=True)
    status = Column(SQLAlchemyEnum(CharacterStatus), nullable=True)  # or use StatusEnum
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)

    # Relationships
    user = relationship("User", back_populates="characters")


class Story(Base):
    __tablename__ = "stories"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=True)
    charachter_ids = Column(
        Text, nullable=True
    )  # JSON-based many-to-many not normalized

    type = Column(String(50), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    status = Column(SQLAlchemyEnum(StoryStatus), nullable=False, default=StoryStatus.draft)
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


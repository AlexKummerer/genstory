import enum
import uuid
from datetime import datetime
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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates, DeclarativeBase


Base: DeclarativeBase = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CharacterStatus(str, enum.Enum):
    draft = "draft"
    generated = "generated"
    finalized = "finalized"


class StoryStatus(str, enum.Enum):
    draft = "draft"
    generated = "generated"
    finalized = "finalized"
    published = "published"
    archived = "archived"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(20), nullable=False, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    characters = relationship("Character", back_populates="user", cascade="all, delete")
    stories = relationship("Story", back_populates="user", cascade="all, delete")

    @validates("email")
    def normalize_email(self, key, value):
        return value.lower()


class Character(BaseModel):
    __tablename__ = "characters"

    id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )  # UUID as String
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    character_name = Column(String(100), nullable=True)
    optimized_name = Column(String(100), nullable=True)
    character_description = Column(Text, nullable=True)
    optimized_description = Column(Text, nullable=True)
    character_traits = Column(JSON, nullable=True)
    optimized_traits = Column(JSON, nullable=True)
    character_story_context = Column(Text, nullable=True)
    optimized_story_context = Column(Text, nullable=True)
    generated_summary = Column(Text, nullable=True)
    status = Column(
        SQLAlchemyEnum(CharacterStatus),
        nullable=False,
        default=CharacterStatus.draft,
        index=True,
    )

    user = relationship("User", back_populates="characters")

    def to_response(self):
        traits = self.character_traits or []
        return {
            "id": self.id,
            "name": self.character_name,
            "optimized_name": self.optimized_name,
            "description": self.character_description,
            "optimized_description": self.optimized_description,
            "traits": traits,
            "optimized_traits": self.optimized_traits,
            "status": self.status.value,
        }


class Story(BaseModel):
    __tablename__ = "stories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    optimized_title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    optimized_description = Column(Text, nullable=True)
    character_ids = Column(JSON, nullable=True)
    character_roles = Column(JSON, nullable=True)
    content = Column(JSON, nullable=True)
    status = Column(
        SQLAlchemyEnum(StoryStatus),
        nullable=False,
        default=StoryStatus.draft,
        index=True,
    )

    user = relationship("User", back_populates="stories")

    def to_response(self):
        return {
            "id": self.id,
            "title": self.title,
            "optimized_title": self.optimized_title,
            "description": self.description,
            "optimized_description": self.optimized_description,
            "character_ids": self.character_ids,
            "character_roles": self.character_roles,
            "content": self.content,
            "status": self.status.value,
        }

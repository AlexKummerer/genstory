from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.utils.openai_client import CharacterRole, FullStoryDetails


class StoryResponse(BaseModel):
    id: str
    title: Optional[str]
    optimized_title: Optional[str]
    description: str
    optimized_description: Optional[str]
    character_ids: List[str]
    character_roles: Optional[List[CharacterRole]]
    content: Optional[FullStoryDetails]
    cover_image_id: Optional[str]
    status: str


class StoryBasicUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]

    @field_validator("description")
    def validate_description(cls, v):
        if len(v) < 20:
            raise ValueError("Description should be at least 10 characters.")
        return v

    @field_validator("title")
    def validate_title(cls, v):
        if len(v) < 5:
            raise ValueError("Title should be at least 10 characters.")
        return v


class StoryInput(BaseModel):
    title: Optional[str]
    description: str
    character_ids: List[str]

    @field_validator("character_ids")
    def validate_character_ids(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 characters are required.")
        return v

    @field_validator("description")
    def validate_description(cls, v):
        if len(v) < 20:
            raise ValueError("Description should be at least 10 characters.")
        return v

    @field_validator("title")
    def validate_title(cls, v):
        if len(v) < 5:
            raise ValueError("Title should be at least 10 characters.")
        return v


class ImageResponse(BaseModel):
    id: str
    story_id: str
    base64_data: str

class ImageDownloadResponse(BaseModel):
    message: str
    file_path: str

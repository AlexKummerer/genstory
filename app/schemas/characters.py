from pydantic import BaseModel, Field
from typing import List, Optional

from app.schemas.traits import Trait


class CharacterInput(BaseModel):
    name: Optional[str] = Field(None, max_length=100, min_length=4)
    description: str = Field(..., max_length=1000, min_length=10)
    traits: Optional[List[Trait]]


class CharacterResponse(BaseModel):
    id: str
    name: Optional[str]
    optimized_name: Optional[str]
    description: str
    optimized_description: Optional[str]
    traits: Optional[List[Trait]]
    optimized_traits: Optional[List[Trait]]
    status: str

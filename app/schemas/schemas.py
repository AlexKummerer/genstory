from typing import Optional
from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate


class UserRead(BaseUser):
    username: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False  # Default value provided


class UserCreate(BaseUserCreate):
    username: str
    is_active: bool = True  # Default value provided
    is_superuser: bool = False  # Default value provided
    is_verified: bool = False  # Default value provided


class UserUpdate(BaseUserUpdate):
    username: Optional[str] = None

from fastapi import APIRouter
from app.schemas.schemas import UserCreate, UserRead, UserUpdate
from app.users.user import active_user, auth_backend, fastapi_users
from app.core.config import settings

router = APIRouter()

router.include_router(
    fastapi_users.get_users_router(
        UserRead,
        UserUpdate,
        False,
    ),
    prefix="/users",
    tags=["users"],
)

current_user = fastapi_users.current_user()

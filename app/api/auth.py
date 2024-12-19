from fastapi import APIRouter, Depends
from app.db.models import User
from app.schemas.schemas import UserCreate, UserRead, UserUpdate
from app.users.user import active_user, auth_backend, fastapi_users


router = APIRouter()


router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)


@router.get("/authenticated-route")
async def authenticated_route(
    user: User = Depends(active_user),
):
    return {"message": f"Hallo von {user.username} mit {user.email}"}

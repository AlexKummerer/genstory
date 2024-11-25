import os

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm

from app.db.db import User, create_db_and_tables
from app.routes import characters
from app.schemas.schemas import UserCreate, UserRead, UserUpdate
from app.users.user import active_user, auth_backend, fastapi_users, inactive_user

app = FastAPI()

app.include_router(characters.router, prefix="/characters", tags=["characters"])

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)


app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)


app.include_router(
    fastapi_users.get_users_router(active_user, UserRead, UserUpdate),
    prefix="/users/active",
    tags=["users"],
)

app.include_router(
    fastapi_users.get_users_router(inactive_user, UserRead, UserUpdate),
    prefix="/users/inactive",
    tags=["users"],
)


# @app.on_event("startup")
# async def startup_event():
#     await create_db_and_tables()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/authenticated-route")
async def authenticated_route(
    user: User = Depends(active_user),
):
    return {"message": f"Hallo von {user.username} mit {user.email}"}


# @app.on_event("shutdown")
# async def shutdown_event():
#     os.remove("./test.db")

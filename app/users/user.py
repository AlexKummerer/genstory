from typing import Optional
from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase

from app.db.db import async_session_maker, engine, get_user_db
from app.db.models import User

SECRET = "mysupersecretkey"


class UserManager(UUIDIDMixin, BaseUserManager):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_verify(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has been verified.")

    async def on_after_update(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has been updated.")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

    async def on_after_reset_password(
        self, user: User, request: Optional[Request] = None
    ):
        print(f"User {user.id} has reset their password.")

    async def on_after_login(
        self,
        user: User,
        request: Request | None = None,
        response: Response | None = None,
    ) -> None:
        print(f"User {user.id} has logged in.")
        print(f"Request: {request.json()}")
        print(f"Response: {response.body}")
        
        

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):

    yield UserManager(user_db)


cookie_transport = BearerTransport(tokenUrl="/auth/jwt/login")


def get_jwt_strategy():
    return JWTStrategy(
        secret=SECRET, lifetime_seconds=3600, token_audience="fastapi-users:auth"
    )


auth_backend = AuthenticationBackend(
    name="jwt", transport=cookie_transport, get_strategy=get_jwt_strategy
)

fastapi_users = FastAPIUsers(
    get_user_manager=get_user_manager, auth_backends=[auth_backend]
)

active_user = fastapi_users.current_user(active=True)
inactive_user = fastapi_users.current_user(active=False)

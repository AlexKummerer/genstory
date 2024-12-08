from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase

from app.db.db import async_session_maker, engine, get_user_db

SECRET = "mysupersecretkey"


class UserManager(UUIDIDMixin, BaseUserManager):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = BearerTransport(
    tokenUrl="/auth/jwt/login"
)


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

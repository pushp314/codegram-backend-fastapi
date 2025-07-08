import os
import uuid
from fastapi import Depends, HTTPException, APIRouter
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import BearerTransport, JWTStrategy, AuthenticationBackend
from fastapi_users.db import SQLAlchemyUserDatabase
from auth.db import User, get_user_db
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

SECRET = os.getenv("SECRET")
ALGORITHM = os.getenv("ALGORITHM")

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    async def authenticate(self, credentials):
        user = await super().authenticate(credentials)
        if user and not user.is_verified:
            raise HTTPException(status_code=400, detail="Email not verified. Please check your inbox.")
        return user

async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True,verified=True, superuser=True)




import os
import uuid
import datetime
import jwt
from typing import Optional
from fastapi import Depends, Request, HTTPException, APIRouter
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import BearerTransport, JWTStrategy, AuthenticationBackend
from fastapi_users.db import SQLAlchemyUserDatabase
from auth.auth_email import send_email
from auth.db import User, get_user_db, OAuthAccount, async_session_maker
from passlib.context import CryptContext

router = APIRouter()

SECRET = "SECRET"

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_verify_token(email: str):
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    payload = {"sub": email, "exp": expiration.timestamp()}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return token

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def authenticate(self, credentials):
        user = await super().authenticate(credentials)
        if user and not user.is_verified:
            raise HTTPException(status_code=400, detail="Email not verified. Please check your inbox.")
        return user

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered. Email: {user.email}")
        token = create_verify_token(user.email)
        verification_link = f"http://127.0.0.1:8000/auth/custom-verify?token={token}"
        subject = "Verify your email"
        body = (
            f"Hello,\n\nPlease click the following link to verify your email:\n"
            f"{verification_link}\n\nThank you!"
        )
        await send_email(user.email, subject, body)

    async def resend_verification_link(self, email: str):
        user = await self.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.is_verified:
            return {"message": "User is already verified"}

        token = create_verify_token(email)
        verification_link = f"http://127.0.0.1:8000/auth/custom-verify?token={token}"
        subject = "Verify your email"
        body = (
            f"Hello,\n\nPlease click the following link to verify your email:\n"
            f"{verification_link}\n\nThank you!"
        )
        await send_email(email, subject, body)
        return {"message": "Verification email resent successfully"}

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

# Configure the auth backend using BearerTransport.
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




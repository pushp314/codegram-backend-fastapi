from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from httpx_oauth.clients.github import GitHubOAuth2
import httpx
from auth.db import User, async_session_maker
from auth.models import User_Profile
from sqlalchemy.future import select
from passlib.context import CryptContext
import jwt
import datetime
from auth.db import OAuthAccount
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


SECRET = os.getenv("SECRET")
ALGORITHM = os.getenv("ALGORITHM")


def create_access_token(user_id: str, email: str) -> str:
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expiration.timestamp()),
        "type": "access"
    }
    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    return token

def create_refresh_token(user_id: str, email: str) -> str:
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)  # longer expiry
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expiration.timestamp()),
        "type": "refresh"
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)



GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

github_oauth_client = GitHubOAuth2(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

@router.get("/auth/github/login")
async def github_login():
    return await github_oauth_client.get_authorization_url(
        redirect_uri="http://localhost:8000/auth/github/callback",
        state="random_state_string"
    )

@router.get("/auth/github/callback")
async def github_callback(request: Request):
    code = request.query_params.get("code")
    token = await github_oauth_client.get_access_token(
        code=code,
        redirect_uri="http://localhost:8000/auth/github/callback"
    )

    if "access_token" not in token:
        return JSONResponse({
            "error": "Failed to get access token from GitHub",
            "github_response": token
        }, status_code=400)

    access_token = token["access_token"]

    async with httpx.AsyncClient() as client:
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        email_response.raise_for_status()
        email_data = email_response.json()
        print(f"email data = {email_data} ")

        github_email = None
        for email_entry in email_data:
            if email_entry.get("primary"):
                github_email = email_entry.get("email")
                break
        if not github_email:
            github_email = email_data[0].get("email") if email_data else None
            print(f"github_email data = {github_email} ")



        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_response.raise_for_status()
        user_data = user_response.json()
        github_username = user_data.get("login")

    # --- DB Logic ---
    async with async_session_maker() as session:
        # 1. Upsert User

        result = await session.execute(select(User).where(User.email == github_email))
        user = result.unique().scalar_one_or_none()

        if user:
              return JSONResponse({
           "message": "User already exists",
          "jwt_token": create_access_token(str(user.id), github_email),
           "refresh_token": create_refresh_token(str(user.id), github_email)
        }, status_code=200)

          

        else:
            user = User(
                email=github_email,
                username=github_username,
                hashed_password=pwd_context.hash("github_oauth_no_password"),
                is_active=True,
                is_verified=True,
                is_superuser=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            oauth_account = OAuthAccount(
            oauth_name="github",
            access_token=access_token,
            account_id=str(user_data.get("id")),
            account_email=github_email,
            user_id=user.id
                             )
            session.add(oauth_account)
            await session.commit()

        # 2. Upsert User_Profile
        result = await session.execute(select(User_Profile).where(User_Profile.github_id == user_data.get("id")))
        profile = result.scalar_one_or_none()
        profile_fields = {
            "github_id": user_data.get("id"),
            "user_id": str(user.id),  # UUID to string
            "login": user_data.get("login"),
            "node_id": user_data.get("node_id"),
            "avatar_url": user_data.get("avatar_url"),
            "gravatar_id": user_data.get("gravatar_id"),
            "url": user_data.get("url"),
            "html_url": user_data.get("html_url"),
            "followers_url": user_data.get("followers_url"),
            "following_url": user_data.get("following_url"),
            "gists_url": user_data.get("gists_url"),
            "starred_url": user_data.get("starred_url"),
            "subscriptions_url": user_data.get("subscriptions_url"),
            "organizations_url": user_data.get("organizations_url"),
            "repos_url": user_data.get("repos_url"),
            "events_url": user_data.get("events_url"),
            "received_events_url": user_data.get("received_events_url"),
            "type": user_data.get("type"),
            "user_view_type": user_data.get("user_view_type"),
            "site_admin": user_data.get("site_admin"),
            "name": user_data.get("name"),
            "company": user_data.get("company"),
            "blog": user_data.get("blog"),
            "location": user_data.get("location"),
            "email": github_email,
            "hireable": user_data.get("hireable"),
            "bio": user_data.get("bio"),
            "twitter_username": user_data.get("twitter_username"),
            "notification_email": user_data.get("notification_email"),
            "public_repos": user_data.get("public_repos"),
            "public_gists": user_data.get("public_gists"),
            "followers": user_data.get("followers"),
            "following": user_data.get("following"),
            "created_at": user_data.get("created_at"),
            "updated_at": user_data.get("updated_at"),
            "private_gists": user_data.get("private_gists"),
            "total_private_repos": user_data.get("total_private_repos"),
            "owned_private_repos": user_data.get("owned_private_repos"),
            "disk_usage": user_data.get("disk_usage"),
            "collaborators": user_data.get("collaborators"),
            "two_factor_authentication": user_data.get("two_factor_authentication"),
            "plan": user_data.get("plan"),
        }
        if profile:
            for key, value in profile_fields.items():
                setattr(profile, key, value)
        else:
            profile = User_Profile(**profile_fields)
            session.add(profile)
        await session.commit()

        jwt_token = create_access_token(str(user.id), github_email)
        refresh_token = create_refresh_token(str(user.id), github_email)


        


        return JSONResponse({
            "message": "login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser
            },
            "jwt_token": jwt_token,
            "refresh_token": refresh_token,
            "profile": user_data
        })
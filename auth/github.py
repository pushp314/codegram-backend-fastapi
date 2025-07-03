from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from httpx_oauth.clients.github import GitHubOAuth2
import httpx

from auth.db import User, async_session_maker  # adjust as per your project
from sqlalchemy.future import select
from passlib.context import CryptContext
import jwt
import datetime


SECRET = "SECRET"  # Use a secure secret key!
ALGORITHM = "HS256"

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

GITHUB_CLIENT_ID = "Ov23liGyvkKJuwNoaHRs"
GITHUB_CLIENT_SECRET = "b8547e77b269a8f381721a130445592517759722"

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
    state = request.query_params.get("state")

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
        # Email API call
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        email_response.raise_for_status()
        email_data = email_response.json()

        # Get primary email
        github_email = None
        for email_entry in email_data:
            if email_entry.get("primary"):
                github_email = email_entry.get("email")
                break
        if not github_email:
            github_email = email_data[0].get("email") if email_data else None

        # User API call
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_response.raise_for_status()
        user_data = user_response.json()
        github_username = user_data.get("login")

    # --- DB Logic ---
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == github_email))
        user = result.unique().scalar_one_or_none()

        # JWT token must use your DB user's id, not the GitHub user_data id!
        user_id_for_jwt = str(user.id) if user else github_username  # fallback if new
        jwt_token = create_access_token(str(user_data["id"]), github_email)


        if user:
            return JSONResponse({
                "message": "user already exists",
                "user": user_data,
                "jwt_token": jwt_token,
            })
        else:
            try:
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
                jwt_token = create_access_token(str(user.id), github_email)
                return JSONResponse({
                    "message": "user created",
                    "user": user_data,
                    "jwt_token": jwt_token,
                })
            except Exception as e:
                return JSONResponse({
                    "error": str(e)
                }, status_code=500)
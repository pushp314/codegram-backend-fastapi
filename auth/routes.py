from fastapi import APIRouter, HTTPException
from auth.models import User_Profile
from auth.db import async_session_maker
from sqlalchemy.future import select
import httpx



router = APIRouter()

@router.get("/profile/{github_id}")
async def get_user_profile(github_id: int):
    async with async_session_maker() as session:
        result = await session.execute(select(User_Profile).where(User_Profile.github_id == github_id))
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    

@router.get("/followers/{username}")
async def get_github_followers(username: str):
    url = f"https://api.github.com/users/{username}/followers"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="GitHub API error")

    return response.json()


@router.get("/following/{username}")
async def get_github_following(username: str):
    url = f"https://api.github.com/users/{username}/following"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="GitHub API error")

    return response.json()



@router.get("/starred/{username}")
async def get_github_user_starred(username: str):
    url = f"https://api.github.com/users/{username}/starred"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="GitHub API error")

    return response.json()



@router.get("/get_others_repo_info/{username}")
async def get_github_others_repo(username: str):
    url = f"https://api.github.com/users/{username}/repos"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="GitHub API error")

    return response.json()

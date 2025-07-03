from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import ORJSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import datetime
import urllib.parse
import jwt
from fastapi.responses import JSONResponse
from fastapi import Body
from .auth_email import send_email
import datetime
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import uuid
from auth.db import User, create_db_and_tables, async_session_maker, OAuthAccount
from auth.schemas import UserCreate, UserRead, UserUpdate
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
import datetime
import jwt
import urllib.parse
from sqlalchemy.future import select  
from auth.users import  SECRET
from auth.db import User, OAuthAccount, async_session_maker

from passlib.context import CryptContext
from auth.users import (
    auth_backend,
    current_active_user,
    current_superuser,
    current_verified_user,
    fastapi_users,
    SECRET,  # SECRET should be defined in app/users.py
)


from auth.users import router as users_router
from startapp.routes import router as animal_router


from .github import router as github_router

app = FastAPI(default_response_class=ORJSONResponse)


app.include_router(github_router, tags=["Github Auth"])

app.include_router(users_router,tags=["auth"])
app.include_router(animal_router,tags=["animal"])  





origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from auth.db import User, get_async_session
from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class UserSchema(BaseModel):
    id: UUID
    email: str
    is_active: bool
    is_verified: bool  # Add
    is_superuser: bool  # Add
    username: Optional[str] = None

    
    class Config:
        from_attributes = True
    

class UserUpdateSchema(BaseModel):
    email: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None  # Add
    username: str
    is_superuser: bool

class UserCreateSchema(BaseModel):
    email: str
    password: str
    is_active: bool = True
    is_verified: bool = False  # Add default
    is_superuser: bool = False
    username: Optional[str] = None




@app.get("/admin/usersall", response_model=list[UserSchema])
async def getdb_data(user: User = Depends(current_superuser),session: AsyncSession = Depends(get_async_session)):

    result = await session.execute(select(User))
    print(f"result data == ",result)
    users = result.unique().scalars().all()

    users_pydantic = [UserSchema.model_validate(user) for user in users]

    return users_pydantic


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


@app.post("/admin/newusers", response_model=UserSchema)
async def create_user(user_create: UserCreateSchema, session: AsyncSession = Depends(get_async_session), user = Depends(current_superuser)):
    hashed_password = get_password_hash(user_create.password)
    # Assuming your User model accepts: email, hashed_password, is_active
    db_user = User(email=user_create.email, username=user_create.username, hashed_password=hashed_password, is_active=user_create.is_active,  is_verified=user_create.is_verified,is_superuser=user_create.is_superuser)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user




@app.get("/admin/users/{user_id}", response_model=UserSchema)
async def get_user(user_id: UUID, session: AsyncSession = Depends(get_async_session), user=Depends(current_superuser)):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



@app.patch("/admin/users/{user_id}", response_model=UserSchema)
async def update_user(user_id: UUID, user_update: UserUpdateSchema, 
                     session: AsyncSession = Depends(get_async_session), 
                     user=Depends(current_superuser)):
    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update all fields
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.username is not None:
        db_user.username = user_update.username
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active
    if user_update.is_verified is not None:  # Add
        db_user.is_verified = user_update.is_verified
    if user_update.is_superuser is not None:  # Add
        db_user.is_superuser = user_update.is_superuser

    await session.commit()
    await session.refresh(db_user)
    return db_user


@app.delete("/admin/users/{user_id}" ,status_code=204)
async def delete_user(user_id: UUID, session: AsyncSession = Depends(get_async_session), user=Depends(current_superuser)):
    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(db_user)
    await session.commit()
    return {"detail": "User deleted successfully"}


from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
templates = Jinja2Templates(directory="auth/templates")



def create_reset_token(email: str) -> str:
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    payload = {"sub": email, "exp": int(expiration.timestamp()), "type": "reset"}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return token



app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)



@app.get("/json-test",  tags=["test"])
async def json_test():
    return {"message": "Hello!", "date": datetime.datetime.now()}



@app.get("/authenticated-route" , tags=["test"])
async def authenticated_route(user: User = Depends(current_superuser)):
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Email not verified")
    return {"message": f"Hello super admin  {user.email}!"}



@app.get("/login-user-route" , tags=["test"])
async def login_user_route(user: User = Depends(current_verified_user)):
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Email not verified")
    return {"message": f"Hello local user  {user.email}!"}


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()




from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


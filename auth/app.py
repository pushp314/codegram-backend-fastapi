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
from projects.routes import router as project_router


from .github import get_github_oauth_router

app = FastAPI(default_response_class=ORJSONResponse)


github_router = get_github_oauth_router(fastapi_users, auth_backend)
app.include_router(github_router, prefix="/auth/github")

app.include_router(users_router,tags=["auth"])
app.include_router(animal_router,tags=["animal"])  
app.include_router(project_router,tags=["Projects"])  





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





# @app.get("/users/all")
# async def users_all(user: User = Depends(current_superuser),session: AsyncSession= Depends(get_async_session)):
#     result = await session.execute(select(User))
#     print(f"result data == ",result)
#     users = result.unique().scalars().all()
#     return users



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


@app.get("/adminui", response_class=HTMLResponse)
async def admin_ui(request: Request):
    return templates.TemplateResponse("AdminUI.html", {"request": request})


@app.get("/hybrid",response_class=HTMLResponse)
async def hybrid_ui(request:Request):
    return templates.TemplateResponse("HybridPanel.html",{"request": request})









def create_reset_token(email: str) -> str:
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    payload = {"sub": email, "exp": int(expiration.timestamp()), "type": "reset"}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return token


@app.post("/auth/forgot-password")
async def forgot_password(data: dict = Body(...)):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    from fastapi_users.db import SQLAlchemyUserDatabase
    async with async_session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User, OAuthAccount)
        user = await user_db.get_by_email(email)
        if user:
            reset_token = create_reset_token(email)
            reset_link = f"http://127.0.0.1:8000/auth/custom-reset?token={reset_token}"
            subject = "Reset Your Password"
            body = f"Please click the link below to reset your password:\n{reset_link}"
            await send_email(email, subject, body)
    
    return {"message": "If the email exists, a reset link has been sent."}




# Ye Password Reset ke Liye hai 
@app.get("/auth/custom-reset" , tags=["auth"])
async def custom_reset(request: Request):
    token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        if payload.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Invalid token type")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token error: {str(e)}")
    
    # Redirect the user to your React reset-password page, passing along the token.
    # return JSONResponse(
    #     content={
    #         "message": "Token validated for password reset.",
    #         "email": email,
    #         "token": token
    #     }
    # )
    react_redirect_url = f"http://localhost:5173/reset-password?token={urllib.parse.quote(token)}"
    return RedirectResponse(url=react_redirect_url)



class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# New password save karne ke liye use hota hai jab React frontend se user ne token + new password bheja ho
@app.post("/auth/reset-password" , tags=["auth"])
async def reset_password(data: ResetPasswordRequest):
    token = data.token
    new_password = data.new_password
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        if payload.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Invalid token type")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token error: {str(e)}")
    
    from fastapi_users.db import SQLAlchemyUserDatabase
    async with async_session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User, OAuthAccount)
        user = await user_db.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update the user's password (hashed)
        new_hashed = get_password_hash(new_password)
        user.hashed_password = new_hashed
        await session.commit()
    
    return {"message": "Password updated successfully"}


app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])





# ye Email Verify Ka hai 
@app.get("/auth/custom-verify", tags=["auth"])
async def custom_verify(request: Request):
    token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token error: {str(e)}")
    
    from fastapi_users.db import SQLAlchemyUserDatabase
    async with async_session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User, OAuthAccount)
        user = await user_db.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_verified = True
        await session.commit()
    
    # return JSONResponse(content={"message": "User verified successfully", "email": email})
    react_redirect_url = "http://localhost:5173/auth/callback?verified=true"
    return RedirectResponse(url=react_redirect_url)





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









#Google Auth Logic


from httpx_oauth.clients.google import GoogleOAuth2

SECRET = "SECRET"


google_oauth_client = GoogleOAuth2(
    client_id="619376530474-httooklsail7hr0gf1r2iudicgd2bc29.apps.googleusercontent.com",
    client_secret="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",
    scopes=["openid", "email", "profile"]
)


async def get_google_user_info(token: str):
    try:
        user_data = await google_oauth_client.get_id_email(token)
        print("✅ Google User Data:", user_data)
        return user_data
    except Exception as e:
        print("❌ Error Fetching Google User Info:", str(e))
        return None

@app.get("/auth/google/custom-callback" ,tags=["auth"])
async def custom_google_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    try:
        token_data = await google_oauth_client.get_access_token(
            code,
            redirect_uri="http://127.0.0.1:8000/auth/google/custom-callback"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching Google access token: {str(e)}")

    try:
        google_user_info = await google_oauth_client.get_id_email(token_data["access_token"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching Google user info: {str(e)}")

    user = await get_or_create_user_from_google(google_user_info)
    if not user:
        raise HTTPException(status_code=400, detail="Could not get or create user")

    if isinstance(google_user_info, tuple):
        google_id, email = google_user_info
    else:
        email = google_user_info.get("email")
        google_id = google_user_info.get("sub")

    expires_in = token_data.get("expires_in", 0)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)

    async with async_session_maker() as session:
        result = await session.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user.id,
                OAuthAccount.oauth_name == "google"
            )
        )
        existing_account = result.scalar_one_or_none()
        if existing_account:
            existing_account.access_token = token_data["access_token"]
            existing_account.refresh_token = token_data.get("refresh_token")
            existing_account.expires_at = expires_at
            existing_account.account_id = google_id
            existing_account.account_email = email
        else:
            new_oauth = OAuthAccount(
                user_id=user.id,
                oauth_name="google",
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=expires_at,
                account_id=google_id,
                account_email=email,
            )
            session.add(new_oauth)
        await session.commit()

    payload = {
        "sub": str(user.id),
        "aud": ["fastapi-users:auth"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=3600)
    }
    backend_token = jwt.encode(payload, SECRET, algorithm="HS256")

    react_redirect_url = f"http://localhost:5173/auth/callback?token={urllib.parse.quote(backend_token)}&verified=true"
    return RedirectResponse(url=react_redirect_url)


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_or_create_user_from_google(user_info) -> User:
    if isinstance(user_info, tuple):
        try:
            google_id, email = user_info  
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid user info format from Google")
    elif isinstance(user_info, dict):
        email = user_info.get("email")
    else:
        raise HTTPException(status_code=400, detail="Unexpected user info format from Google")
    
    if not email:
        raise HTTPException(status_code=400, detail="Google did not provide an email")
    
    from fastapi_users.db import SQLAlchemyUserDatabase
    async with async_session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User, OAuthAccount)
        existing_user = await user_db.get_by_email(email)
        if existing_user:
            if not existing_user.is_verified:
                existing_user.is_verified = True
                await session.commit()
            return existing_user
        else:
            import uuid
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            random_password = uuid.uuid4().hex 
            dummy_hashed = pwd_context.hash(random_password)  
            
            new_user_data = {"email": email, "hashed_password": dummy_hashed, "is_verified": True}
            new_user = await user_db.create(new_user_data)
            return new_user

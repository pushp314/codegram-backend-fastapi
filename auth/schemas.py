import uuid
from typing import Optional

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None
    username: Optional[str] =None


class UserCreate(schemas.BaseUserCreate):
    username: Optional[str] =None


class UserUpdate(schemas.BaseUserUpdate):
    is_verified: Optional[bool] = None
    is_superuser: Optional[bool] = None
    username: Optional[str] =None

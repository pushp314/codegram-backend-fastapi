from pydantic import BaseModel, Field
from typing import List, Optional


class SuccessResponse(BaseModel):
    message: str


class TechnologyRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TechnologyCreate(BaseModel):
    name: str


class ProjectCreate(BaseModel):
    title: str
    description: str
    image_url: Optional[str] = None
    price: int
    purchase_type: str
    rating: Optional[float] = 0.0
    reviews_count: Optional[int] = 0
    support_duration_months: Optional[int] = 6
    includes: Optional[str] = None  # or List[str] if you're using JSON
    technologies: List[str]


class ProjectRead(BaseModel):
    id: int
    title: str
    description: str
    image_url: Optional[str] = None
    price: int
    purchase_type: str
    rating: float
    reviews_count: int
    support_duration_months: int
    includes: Optional[str]
    technologies: List[str]

    class Config:
        from_attributes = True

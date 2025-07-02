from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from auth.db import get_async_session  # Reusing existing session dependency
from startapp.models import Animal

router = APIRouter()

@router.get("/")
async def get_animals(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Animal))
    animals = result.scalars().all()
    return animals

@router.post("/")
async def create_animal(name: str, species: str, session: AsyncSession = Depends(get_async_session)):
    # Check if animal already exists (optional)
    result = await session.execute(select(Animal).filter(Animal.name == name))
    existing_animal = result.scalars().first()
    if existing_animal:
        raise HTTPException(status_code=400, detail="Animal already exists")
    
    animal = Animal(name=name, species=species)
    session.add(animal)
    await session.commit()
    await session.refresh(animal)
    return animal

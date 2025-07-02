from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from auth.db import get_async_session  
from projects.models import Project,Technology
from sqlalchemy.orm import selectinload
from .schemas import ProjectRead ,ProjectCreate,SuccessResponse
from fastapi import HTTPException
import traceback
from fastapi import status


from typing import List

router = APIRouter()

@router.get("/pro", response_model=List[ProjectRead])
async def get_projects(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Project).options(selectinload(Project.technologies))
    )
    return result.scalars().all()


@router.get("/pro/{project_id}", response_model=ProjectRead)
async def get_project_by_id(project_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Project).options(selectinload(Project.technologies)).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/pro", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, session: AsyncSession = Depends(get_async_session)):
    try:
        new_project = Project(
            title=project.title,
            description=project.description,
            image_url=project.image_url,
            price=project.price,
            purchase_type=project.purchase_type,
            rating=project.rating,
            reviews_count=project.reviews_count,
            support_duration_months=project.support_duration_months,
            includes=project.includes
        )

        for tech_name in project.technologies:
            new_project.technologies.append(Technology(name=tech_name))

        session.add(new_project)
        await session.commit()
        await session.refresh(new_project)

        return SuccessResponse(message="Project created successfully")
    except Exception as e:
        print("\nERROR OCCURRED:\n")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create project")




@router.put("/pro/{project_id}", response_model=SuccessResponse)
async def update_project(
    project_id: int,
    project: ProjectCreate,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        # 1. Get existing project
        result = await session.execute(
            select(Project)
            .options(selectinload(Project.technologies))
            .where(Project.id == project_id)
        )
        existing_project = result.scalar_one_or_none()

        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 2. Update basic fields
        existing_project.title = project.title
        existing_project.description = project.description
        existing_project.price = project.price

        existing_project.purchase_type = project.purchase_type
        existing_project.rating = project.rating
        existing_project.reviews_count = project.reviews_count

        existing_project.support_duration_months = project.support_duration_months
        existing_project.includes = project.includes
        
        for tech in existing_project.technologies:
            await session.delete(tech)

        await session.flush()  # Ensure deletes are done

        # 4. Add new technologies
        for tech_name in project.technologies:
            existing_project.technologies.append(Technology(name=tech_name))

        await session.commit()
        await session.refresh(existing_project)

        return SuccessResponse(message="project data updated successfully")

    except Exception as e:
        print("\nUPDATE ERROR:\n")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/pro/{project_id}", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def delete_project(project_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await session.delete(project)
    await session.commit()

    return SuccessResponse(message=f"Project with id {project_id} deleted successfully.")

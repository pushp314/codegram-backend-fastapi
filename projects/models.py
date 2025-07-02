from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,Float,Text
from sqlalchemy.orm import relationship
from datetime import datetime
from auth.db import Base, User  

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    image_url = Column(String, nullable=True)
    technologies = relationship("Technology", back_populates="project")

    price = Column(Integer)  # ₹999
    purchase_type = Column(String)  # e.g., "One-time purchase"
    rating = Column(Float, default=0.0)  # e.g., 4.8
    reviews_count = Column(Integer, default=0)  # e.g., 124
    support_duration_months = Column(Integer, default=6)

    # Comma-separated or JSON string
    includes = Column(Text, nullable=True)  # e.g., "source code, support, guide"

    technologies = relationship("Technology", back_populates="project")


class Technology(Base):
    __tablename__ = "technologies"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship("Project", back_populates="technologies")



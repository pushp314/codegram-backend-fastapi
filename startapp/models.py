from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from auth.db import Base, User  # Reusing Base from auth/db.py


class Animal(Base):
    __tablename__ = "animals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    species = Column(String, index=True)
    



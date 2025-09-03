from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    files = relationship("File", back_populates="owner")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    path = Column(String)
    mime_type = Column(String)
    size = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))
    parent_folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ai_tags = Column(Text)  # JSON string of AI-generated tags
    embedding = Column(Text)  # Vector embedding for semantic search
    
    owner = relationship("User", back_populates="files")
    parent_folder = relationship("Folder", back_populates="files")

class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    parent_folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    files = relationship("File", back_populates="parent_folder")
    subfolders = relationship("Folder")

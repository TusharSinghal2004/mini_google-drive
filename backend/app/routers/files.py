from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import json
from minio import Minio
from sentence_transformers import SentenceTransformer
import magic
import os

from ..database import get_db
from ..models.models import File as FileModel, User
from .users import get_current_user

router = APIRouter()

# Initialize MinIO client
minio_client = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Read file content
    content = await file.read()
    
    # Detect MIME type
    mime_type = magic.from_buffer(content, mime=True)
    
    # Generate file path in MinIO
    file_path = f"{current_user.id}/{file.filename}"
    
    # Upload to MinIO
    minio_client.put_object(
        "mini-drive",
        file_path,
        file.file,
        length=-1,
        content_type=mime_type
    )
    
    # Generate AI tags and embeddings
    # This is a simple example - you might want to process the file differently based on type
    text_content = file.filename  # Using filename for demonstration
    embedding = model.encode(text_content).tolist()
    ai_tags = ["document", "text"]  # Placeholder - implement actual AI tagging
    
    # Create database entry
    db_file = FileModel(
        name=file.filename,
        path=file_path,
        mime_type=mime_type,
        size=len(content),
        owner_id=current_user.id,
        parent_folder_id=folder_id,
        ai_tags=json.dumps(ai_tags),
        embedding=json.dumps(embedding)
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return {
        "message": "File uploaded successfully",
        "file_id": db_file.id,
        "file_name": db_file.name
    }

@router.get("/list")
async def list_files(
    folder_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(FileModel).filter(
        FileModel.owner_id == current_user.id,
        FileModel.parent_folder_id == folder_id
    )
    files = query.all()
    
    return [
        {
            "id": file.id,
            "name": file.name,
            "mime_type": file.mime_type,
            "size": file.size,
            "created_at": file.created_at,
            "updated_at": file.updated_at
        }
        for file in files
    ]

@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get file from database
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.owner_id == current_user.id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Generate presigned URL for download
    try:
        url = minio_client.presigned_get_object(
            "mini-drive",
            file.path,
            expires=timedelta(minutes=30)
        )
        return {"download_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generating download URL")

@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get file from database
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.owner_id == current_user.id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from MinIO
    try:
        minio_client.remove_object("mini-drive", file.path)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting file from storage")
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    return {"message": "File deleted successfully"}

@router.get("/search")
async def search_files(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Convert search query to embedding
    query_embedding = model.encode(query).tolist()
    
    # Here you would typically use a vector similarity search
    # For now, we'll just return files with matching names (implement proper vector search later)
    files = db.query(FileModel).filter(
        FileModel.owner_id == current_user.id,
        FileModel.name.ilike(f"%{query}%")
    ).all()
    
    return [
        {
            "id": file.id,
            "name": file.name,
            "mime_type": file.mime_type,
            "size": file.size,
            "created_at": file.created_at,
            "ai_tags": json.loads(file.ai_tags)
        }
        for file in files
    ]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.models import Folder, User
from .users import get_current_user

router = APIRouter()

@router.post("/create")
async def create_folder(
    name: str,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if folder with same name exists in the same location
    existing_folder = db.query(Folder).filter(
        Folder.owner_id == current_user.id,
        Folder.parent_folder_id == parent_id,
        Folder.name == name
    ).first()
    
    if existing_folder:
        raise HTTPException(
            status_code=400,
            detail="A folder with this name already exists in this location"
        )
    
    # Create new folder
    new_folder = Folder(
        name=name,
        owner_id=current_user.id,
        parent_folder_id=parent_id
    )
    
    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)
    
    return {
        "id": new_folder.id,
        "name": new_folder.name,
        "created_at": new_folder.created_at
    }

@router.get("/list")
async def list_folders(
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folders = db.query(Folder).filter(
        Folder.owner_id == current_user.id,
        Folder.parent_folder_id == parent_id
    ).all()
    
    return [
        {
            "id": folder.id,
            "name": folder.name,
            "created_at": folder.created_at
        }
        for folder in folders
    ]

@router.get("/{folder_id}")
async def get_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    return {
        "id": folder.id,
        "name": folder.name,
        "created_at": folder.created_at,
        "parent_folder_id": folder.parent_folder_id
    }

@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check if folder is empty
    if folder.files or folder.subfolders:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete non-empty folder"
        )
    
    db.delete(folder)
    db.commit()
    
    return {"message": "Folder deleted successfully"}

@router.put("/{folder_id}/rename")
async def rename_folder(
    folder_id: int,
    new_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check if folder with new name already exists in the same location
    existing_folder = db.query(Folder).filter(
        Folder.owner_id == current_user.id,
        Folder.parent_folder_id == folder.parent_folder_id,
        Folder.name == new_name,
        Folder.id != folder_id
    ).first()
    
    if existing_folder:
        raise HTTPException(
            status_code=400,
            detail="A folder with this name already exists in this location"
        )
    
    folder.name = new_name
    db.commit()
    
    return {
        "id": folder.id,
        "name": folder.name,
        "created_at": folder.created_at
    }
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import our app modules (we'll create these next)
from app.database import get_db
from app.models import models
from app.routers import users, files, folders

# Create FastAPI app instance
app = FastAPI(
    title="Mini Google Drive",
    description="AI-Optimized Personal Cloud Storage System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(folders.router, prefix="/api/folders", tags=["folders"])

@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running
    """
    return {
        "message": "Welcome to Mini Google Drive API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "database": "connected",  # We'll implement actual DB checking later
        "storage": "connected"    # We'll implement MinIO checking later
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    )

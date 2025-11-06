import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth, jobs, files
from core.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Generations Automation API",
    description="API for automating client notes extraction from Generations IDB system",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this in production to specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(files.router)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Generations Automation API",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Detailed health check"""
    import os
    from pathlib import Path

    return {
        "status": "healthy",
        "database": os.path.exists(settings.database_path),
        "queue_database": os.path.exists(settings.queue_database_path),
        "sessions_dir": Path(settings.sessions_dir).exists()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

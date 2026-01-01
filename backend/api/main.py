"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from core.database.connection import init_database
from api.routes import auth

settings = get_settings()

# Initialize database
init_database(settings.db_path, settings.db_password or "")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)

# Import and include other routers
from api.routes import clusters, projects, jdk, targets
app.include_router(clusters.router)
app.include_router(projects.router)
app.include_router(jdk.router)
app.include_router(targets.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "JDK Compliance Scanner API",
        "version": settings.app_version
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


"""
Main FastAPI application
"""
import logging
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from config.settings import get_settings
from core.database.connection import init_database
from api.routes import auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize database
init_database(settings.db_path, settings.db_password or "")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to catch all unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__
        }
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


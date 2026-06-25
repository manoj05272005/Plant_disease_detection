"""
FastAPI Main Application
Production-ready backend for Crop Disease Detection System
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

import logging
import time

from app.core.config import settings
from app.core.database import Database
from app.api.v1 import api_router
from app.utils.file_handler import FileHandler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

if settings.LOG_FILE:
    logging.getLogger().addHandler(logging.FileHandler(settings.LOG_FILE))

logger = logging.getLogger(__name__)


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events
    """
    # Startup
    logger.info("Starting Crop Disease Detection API...")
    logger.info(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    
    try:
        # Connect to database
        await Database.connect_db()
        logger.info("Database connection established")
        
        # Ensure upload directories exist
        FileHandler.ensure_upload_dir()
        logger.info("Upload directories initialized")
        
        # Load AI models (if needed)
        # from app.services.ai_service import ai_service
        # ai_service.load_models()
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Crop Disease Detection API...")
    
    try:
        # Close database connection
        await Database.close_db()
        logger.info("Database connection closed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Enabled Crop Disease Diagnosis & Remediation System",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# CORS Middleware - Must be added before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex='https?://.*',
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.3f}s "
        f"with status {response.status_code}"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error" if not settings.DEBUG else str(exc)
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Check database connection
        db = Database.get_db()
        await db.command('ping')
        
        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Welcome to Crop Disease Detection API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/.well-known/assetlinks.json", include_in_schema=False)
async def assetlinks():
    """Android Digital Asset Links for passkey association with this domain."""
    package_name = settings.ANDROID_APP_PACKAGE_NAME
    fingerprints = settings.ANDROID_APP_SHA256_CERT_FINGERPRINTS
    if isinstance(fingerprints, str):
        fingerprints = [fingerprints]

    normalized_fingerprints = [fp.strip().upper() for fp in fingerprints if fp and fp.strip()]

    if not package_name or not normalized_fingerprints:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": (
                    "Asset links not configured. Set ANDROID_APP_PACKAGE_NAME and "
                    "ANDROID_APP_SHA256_CERT_FINGERPRINTS."
                )
            },
        )

    return [
        {
            "relation": ["delegate_permission/common.get_login_creds"],
            "target": {
                "namespace": "android_app",
                "package_name": package_name,
                "sha256_cert_fingerprints": normalized_fingerprints,
            },
        }
    ]


# Mount static files for uploads
try:
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
except RuntimeError:
    logger.warning("Upload directory not found, will be created on first upload")


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Run application (for development)
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

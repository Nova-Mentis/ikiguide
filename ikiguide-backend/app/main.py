import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config import settings
from app.api.endpoints import router as api_router, APIError, api_error_handler
from app.models.logger import logger

def create_app() -> FastAPI:
    """
    Application factory for creating FastAPI instance.
    
    :return: Configured FastAPI application
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="API for generating personalized Ikigai paths",
        version="1.1.0",
    )

    # Add global exception handler
    app.add_exception_handler(APIError, api_error_handler)

    # Configure CORS with more robust handling
    cors_origins = settings.CORS_ORIGINS or ["http://localhost:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Include API router
    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    async def startup_event():
        """
        Log application startup with configuration details.
        """
        logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} environment")
        logger.info(f"CORS Origins: {cors_origins}")
        logger.info(f"Logging Level: {settings.LOG_LEVEL}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """
        Log application shutdown.
        """
        logger.info(f"Shutting down {settings.APP_NAME}")

    @app.get("/")
    async def root():
        """
        Root endpoint providing basic API information.
        
        :return: Dictionary with API details
        """
        return {
            "message": "Welcome to IKIGUIDE API!",
            "version": "1.1.0",
            "status": "Running",
            "environment": settings.APP_ENV
        }

    return app

# Create FastAPI application
app = create_app()

# Entry point for running the application directly
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=settings.APP_DEBUG
    )

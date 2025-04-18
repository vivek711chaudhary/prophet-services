from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("prophet_service.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("prophet_main")

try:
    logger.info("Starting Prophet Forecasting Service")
    # Add the project root to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Print current directory for debugging
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Import the router
    logger.info("Importing forecast router...")
    from app.routes.forecast_routes import router as forecast_router
    
    app = FastAPI(title="Prophet Forecasting Service")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Update for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include router with prefix
    app.include_router(forecast_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {"message": "Prophet Forecasting Service is running", "status": "online"}

    logger.info("Prophet Service started successfully")
    
except Exception as e:
    logger.error(f"Error starting Prophet service: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1) 
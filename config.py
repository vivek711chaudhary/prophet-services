from pydantic import BaseSettings
import logging

class Settings(BaseSettings):
    # Expect the MongoDB URI to come from an environment variable
    MONGODB_URI: str
    MODEL_CACHE_DIR: str = "cache"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

# Load settings
settings = Settings()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Loaded settings")
logger.debug(f"MongoDB URI: {settings.MONGODB_URI}")

from pydantic import BaseSettings
import logging

class Settings(BaseSettings):
    # Update this line with your MongoDB URI from Atlas or your cloud provider
    MONGODB_URI: str = "mongodb://localhost:27017/"
    MODEL_CACHE_DIR: str = "cache"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()

# Print settings for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Loaded settings - MongoDB URI: {settings.MONGODB_URI}")

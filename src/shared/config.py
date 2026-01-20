from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Quote API"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/quotes"
    )
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "False").lower() == "true"
    
    # Redis (для кэширования)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # External APIs
    FORISMATIC_API_URL: str = "http://api.forismatic.com/api/1.0/"
    WIKIQUOTE_API_URL: str = "https://ru.wikiquote.org/w/api.php"
    
    # Background tasks
    UPDATE_INTERVAL: int = int(os.getenv("UPDATE_INTERVAL", "3600"))  # seconds
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "5"))
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = os.getenv(
        "BACKEND_CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:8000"
    ).split(",")
    
    # Testing
    TESTING: bool = os.getenv("TESTING", "False").lower() == "true"
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
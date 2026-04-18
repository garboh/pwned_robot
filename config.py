"""
Configuration module for pwned_robot with security best practices.
Handles sensitive credentials and environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic v2 with secure defaults.
    """
    
    # Telegram Bot Configuration
    TELEGRAM_TOKEN: str = Field(..., min_length=1)
    TELEGRAM_ADMIN_IDS: list[int] = Field(default_factory=list)
    
    # Database Configuration
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=3306)
    DB_USER: str = Field(...)
    DB_PASSWORD: str = Field(..., min_length=1)
    DB_NAME: str = Field(default="pwned_robot")
    
    # API Configuration
    HIBP_API_KEY: str = Field(
        ..., 
        description="HaveIBeenPwned API key for authenticated requests"
    )
    HIBP_API_TIMEOUT: int = Field(default=30)
    HIBP_API_BASE_URL: str = Field(default="https://haveibeenpwned.com/api/v3")
    
    # Redis Configuration (for caching and rate limiting)
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    
    # Security Settings
    ENABLE_ANALYTICS: bool = Field(default=False)
    MAX_REQUESTS_PER_MINUTE: int = Field(default=5)
    MAX_REQUESTS_PER_HOUR: int = Field(default=50)
    SESSION_TIMEOUT: int = Field(default=3600)  # 1 hour
    
    # Application Settings
    LOG_LEVEL: str = Field(default="INFO")
    DEBUG: bool = Field(default=False)
    ENABLE_CACHE: bool = Field(default=True)
    CACHE_EXPIRATION: int = Field(default=86400)  # 24 hours
    
    # Webhook Settings (for long-polling alternative)
    WEBHOOK_URL: Optional[str] = Field(default=None)
    WEBHOOK_PORT: int = Field(default=8443)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @field_validator("TELEGRAM_ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v) -> list[int]:
        """Parse comma-separated admin IDs from string or single int."""
        if isinstance(v, str):
            return [int(i.strip()) for i in v.split(",") if i.strip()]
        if isinstance(v, int):
            return [v]
        return v
    
    @property
    def database_url(self) -> str:
        """Generate SQLAlchemy database URL."""
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL."""
        password = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# Global settings instance
settings = Settings()

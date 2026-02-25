"""Configuration Management using Pydantic Settings

Loads environment variables with validation and type checking.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Settings
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production)")
    APP_NAME: str = Field(default="ReflectAI", description="Application name")
    VERSION: str = Field(default="1.0.0", description="API version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Security
    API_KEY_SECRET: str = Field(default="dev-secret-key-change-in-production", description="API secret key")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:19006"],
        description="Allowed CORS origins"
    )
    
    # HuggingFace Settings
    HUGGINGFACE_TOKEN: str | None = Field(default=None, description="HuggingFace API token (optional)")
    SENTIMENT_MODEL: str = Field(
        default="j-hartmann/emotion-english-distilroberta-base",
        description="Sentiment analysis model name"
    )
    
    # Model Configuration
    USE_GPU: bool = Field(default=False, description="Use GPU for inference")
    MODEL_CACHE_DIR: str = Field(default="./models", description="Model cache directory")
    MAX_TEXT_LENGTH: int = Field(default=5000, description="Maximum text length for analysis")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str | None = Field(default=None, description="Log file path")
    
    # Rate Limiting (future use)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="API rate limit per minute")
    
    # Insights Configuration
    MIN_ENTRIES_FOR_INSIGHTS: int = Field(default=3, description="Minimum entries needed for insights")
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value"""
        allowed = ["development", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v.lower()
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    def get_model_device(self) -> str:
        """Get device for ML model (cpu or cuda)"""
        if self.USE_GPU:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        return "cpu"
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"


# Global settings instance
settings = Settings()

# Create model cache directory if it doesn't exist
os.makedirs(settings.MODEL_CACHE_DIR, exist_ok=True)

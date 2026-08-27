"""
DataVista+ Backend Configuration
Environment-based settings management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "DataVista+"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    PORT: int = 8092

    # Security
    SECRET_KEY: str = "datavista-super-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./datavista.db"
    SYNC_DATABASE_URL: Optional[str] = None

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5192",
        "http://localhost:3000",
        "http://localhost",
        "http://127.0.0.1:5192",
        "*",
    ]

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: list = [".csv", ".xlsx", ".xls", ".json"]

    # ML Models
    MODELS_DIR: str = "./models"

    # Reports
    REPORTS_DIR: str = "./reports"

    # OpenAI (optional)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    USE_OPENAI: bool = False

    # NLP
    SPACY_MODEL: str = "en_core_web_sm"
    NLQ_CONFIDENCE_THRESHOLD: float = 0.70

    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

# Ensure required directories exist
for directory in [settings.UPLOAD_DIR, settings.MODELS_DIR, settings.REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

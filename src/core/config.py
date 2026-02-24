from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Mediacorp Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: Optional[str] = "sqlite:///./app.db"

    # Logging
    LOG_LEVEL: str = "INFO"

    # AWS Configuration
    AWS_REGION: str = "ap-southeast-1"
    S3_BUCKET: str = "mdm-content-dev"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    KMS_KEY_ID: Optional[str] = None
    
    # Upload Configuration
    PRESIGNED_URL_EXPIRY: int = 3600  # 1 hour
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 * 1024  # 10 GB
    
    ALLOWED_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Mediacorp Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "secret"
    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    # Bot Settings
    BOT_TOKEN: str
    ADMIN_IDS: List[int] = []
    
    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ff_bot"
    
    # Redis Settings (Railway)
    REDIS_URL: Optional[str] = None
    
    # API Settings
    NIX_API_TOKEN: str
    NIX_BASE_URL: str = "https://salas.nixbot.vip/"
    
    # App Settings
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

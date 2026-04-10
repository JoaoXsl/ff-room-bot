from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Union
from pydantic import field_validator

class Settings(BaseSettings):
    # Bot Settings
    BOT_TOKEN: str
    ADMIN_IDS: Union[List[int], str] = []
    
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

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            # Remove brackets if present
            v = v.replace("[", "").replace("]", "")
            if not v.strip():
                return []
            # Split by comma and convert to int
            try:
                return [int(i.strip()) for i in v.split(",") if i.strip()]
            except ValueError:
                return []
        return v

settings = Settings()

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Environment
    app_env: str = "development"
    app_debug: bool = True
    
    # API settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # Database settings
    postgres_user: str = "ytdub"
    postgres_password: str = "securepassword"
    postgres_db: str = "ytdub_db"
    postgres_host: str = "db"
    postgres_port: int = 5432
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # Redis settings
    redis_host: str = "redis"
    redis_port: int = 6379
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    # API Keys (optional)
    openai_api_key: Optional[str] = None
    google_translate_api_key: Optional[str] = None
    coqui_tts_api_key: Optional[str] = None
    
    # Storage paths
    downloads_dir: str = "downloads"
    processed_dir: str = "processed_videos"
    temp_dir: str = "temp"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
settings = Settings()

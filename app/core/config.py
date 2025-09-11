from typing import Optional, Union
from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: str
    database_url: Optional[PostgresDsn] = None
    
    # Redis configuration
    redis_host: str
    redis_port: str
    redis_url: Optional[RedisDsn] = None
    
    # Application configuration
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000
    
    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False

    def __init__(self, **data):
        super().__init__(**data)
        self.database_url = f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/0"

settings = Settings()
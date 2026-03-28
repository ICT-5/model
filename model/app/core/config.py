from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_DATABASE: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_setting():
    return Settings()

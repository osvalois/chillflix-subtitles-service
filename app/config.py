from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Subtitles API"
    app_version: str = "1.0.0"
    debug: bool = False
    opensubtitles_api_key: str
    opensubtitles_base_url: str = "https://api.opensubtitles.com/api/v1"
    addic7ed_base_url: str = "https://www.addic7ed.com"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
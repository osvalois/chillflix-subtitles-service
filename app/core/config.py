# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Configuración requerida
    OPENSUBTITLES_API_KEY: str

    # Configuración adicional
    app_name: str = "Subtitles API"
    app_version: str = "1.0.0"
    debug: bool = True
    opensubtitles_base_url: str = "https://api.opensubtitles.com/api/v1"
    addic7ed_base_url: str = "https://www.addic7ed.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
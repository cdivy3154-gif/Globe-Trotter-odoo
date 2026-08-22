from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="sqlite:///./globetrotter.db",
        description="SQLite database URL",
    )
    UPLOAD_DIR: str = str(Path.home() / ".globetrotter" / "uploads")
    MAX_UPLOAD_MB: int = 5
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "webp"}
    APP_NAME: str = "GlobeTrotter"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
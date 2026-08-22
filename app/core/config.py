from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = Field(
        default="sqlite:///./globetrotter.db",
        description="SQLite database URL",
    )
    UPLOAD_DIR: str = Field(
        default_factory=lambda: str(Path.home() / ".globetrotter" / "uploads"),
        description="Directory for local image uploads",
    )
    MAX_UPLOAD_MB: int = Field(default=5, ge=1)
    ALLOWED_EXTENSIONS: set[str] = Field(
        default_factory=lambda: {"jpg", "jpeg", "png", "webp"},
        description="Allowed file extensions for uploads",
    )
    APP_NAME: str = Field(default="GlobeTrotter")
    APP_VERSION: str = Field(default="1.0.0")


settings = Settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.exceptions import ValidationError


class UploadService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.trips_dir = self.upload_dir / "trips"
        self.avatars_dir = self.upload_dir / "avatars"
        self.trips_dir.mkdir(parents=True, exist_ok=True)
        self.avatars_dir.mkdir(parents=True, exist_ok=True)

    def _validate_extension(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lstrip(".").lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"File type not allowed. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        return ext

    def save_trip_cover(self, trip_id: str, source_file_path: str) -> str:
        if not os.path.exists(source_file_path):
            raise ValidationError("Selected cover image file does not exist")

        file_size_mb = os.path.getsize(source_file_path) / (1024 * 1024)
        if file_size_mb > settings.MAX_UPLOAD_MB:
            raise ValidationError(f"File size ({file_size_mb:.1f}MB) exceeds {settings.MAX_UPLOAD_MB}MB limit")

        ext = self._validate_extension(source_file_path)
        dest_dir = self.trips_dir / trip_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_filename = f"cover_{uuid.uuid4().hex[:8]}.{ext}"
        dest_path = dest_dir / dest_filename
        shutil.copy2(source_file_path, dest_path)

        return str(dest_path)

    def save_avatar(self, user_id: str, source_file_path: str) -> str:
        if not os.path.exists(source_file_path):
            raise ValidationError("Selected avatar image file does not exist")

        file_size_mb = os.path.getsize(source_file_path) / (1024 * 1024)
        if file_size_mb > settings.MAX_UPLOAD_MB:
            raise ValidationError(f"File size ({file_size_mb:.1f}MB) exceeds {settings.MAX_UPLOAD_MB}MB limit")

        ext = self._validate_extension(source_file_path)
        dest_dir = self.avatars_dir / user_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_filename = f"avatar_{uuid.uuid4().hex[:8]}.{ext}"
        dest_path = dest_dir / dest_filename
        shutil.copy2(source_file_path, dest_path)

        return str(dest_path)

    def delete_file(self, full_path_str: str) -> bool:
        try:
            p = Path(full_path_str)
            if p.exists() and p.is_file():
                p.unlink()
                return True
        except Exception:
            pass
        return False
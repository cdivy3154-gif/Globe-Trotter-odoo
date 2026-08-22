from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    integrity_exception_handler,
    http_exception_handler,
)
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError
from app.api.v1 import auth, trips, cities, sharing, admin, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="GlobeTrotter API",
    description="Travel planning application backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(PydanticValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_exception_handler)
app.add_exception_handler(Exception, http_exception_handler)

# Static files for uploads
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# Routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(trips.router, prefix="/api/v1")
app.include_router(cities.router, prefix="/api/v1")
app.include_router(sharing.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
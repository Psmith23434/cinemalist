from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.api import search as search_router
from app.api import movies as movies_router

app = FastAPI(
    title="CinemaList API",
    description="Personal movie tracking — TMDb-powered backend.",
    version="0.3.0",
)

# CORS — allow Vite dev server and same-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite
        "http://localhost:8000",   # same-origin
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve poster images at /media/posters/<filename>
media_dir = Path(settings.MEDIA_DIR)
media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

# Routers
app.include_router(search_router.router)
app.include_router(movies_router.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "app": "CinemaList", "version": "0.3.0"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}

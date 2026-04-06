from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api import movies, entries, lists, tags, genres, stats, search, sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed exclusively by Alembic (run via launcher.py before uvicorn).
    # Do NOT call Base.metadata.create_all here — it conflicts with Alembic's
    # alembic_version tracking and causes duplicate-table errors on fresh installs.
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="CinemaList API",
    description="Personal movie tracking app — backend API",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS (allows React dev server and future Android app) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files for cached posters ─────────────────────
if os.path.exists(settings.MEDIA_DIR):
    app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

# ── Routers ───────────────────────────────────────────
app.include_router(movies.router,  prefix="/api/movies",  tags=["movies"])
app.include_router(entries.router, prefix="/api/entries", tags=["entries"])
app.include_router(lists.router,   prefix="/api/lists",   tags=["lists"])
app.include_router(tags.router,    prefix="/api/tags",    tags=["tags"])
app.include_router(genres.router,  prefix="/api/genres",  tags=["genres"])
app.include_router(stats.router,   prefix="/api/stats",   tags=["stats"])
app.include_router(search.router,  prefix="/api/search",  tags=["search"])
app.include_router(sync.router,    prefix="/api/sync",    tags=["sync"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

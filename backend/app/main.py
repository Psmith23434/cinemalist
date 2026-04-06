from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api import movies, entries, lists, tags, genres, stats, search, sync, ai

# Path to the React production build (built by `npm run build` in frontend/)
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


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

# ── CORS (allows React dev server and future Android app) ──────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files for cached posters ──────────────────────────────────────────
if os.path.exists(settings.MEDIA_DIR):
    app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(movies.router,  prefix="/api/movies",  tags=["movies"])
app.include_router(entries.router, prefix="/api/entries", tags=["entries"])
app.include_router(lists.router,   prefix="/api/lists",   tags=["lists"])
app.include_router(tags.router,    prefix="/api/tags",    tags=["tags"])
app.include_router(genres.router,  prefix="/api/genres",  tags=["genres"])
app.include_router(stats.router,   prefix="/api/stats",   tags=["stats"])
app.include_router(search.router,  prefix="/api/search",  tags=["search"])
app.include_router(sync.router,    prefix="/api/sync",    tags=["sync"])
app.include_router(ai.router,      prefix="/api/ai",      tags=["ai"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


# ── React SPA — serve production build from backend/static/ ─────────────────────
# IMPORTANT: this must come AFTER all /api/* routers so the catch-all
# does not shadow any API endpoints.
#
# How it works:
#   1. Vite builds the React app to backend/static/ via `npm run build`.
#   2. FastAPI mounts backend/static/ to serve JS/CSS/image assets.
#   3. The catch-all route below returns index.html for ANY path that is not
#      an /api/* route, so React Router handles client-side navigation.
#      Without this, a hard refresh on e.g. /movie/42 returns 404.

_index_html = os.path.join(STATIC_DIR, "index.html")

if os.path.isdir(STATIC_DIR):
    # Serve Vite assets (JS, CSS, images, favicon) — must be mounted BEFORE
    # the catch-all route so asset requests are handled by StaticFiles first.
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="spa-assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_catch_all(full_path: str):
    """Return index.html for all non-API paths (React Router SPA support)."""
    if os.path.isfile(_index_html):
        return FileResponse(_index_html)
    return {"detail": "Frontend not built yet. Run: npm run build (in frontend/)"}

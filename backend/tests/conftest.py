"""
Shared pytest fixtures for the CinemaList backend test suite.

Key design decisions:
- Uses an in-memory SQLite database — your real cinemalist.db is NEVER touched.
- Each test gets a fresh database (function-scoped) so tests are fully isolated.
- The FastAPI app's get_db() dependency is overridden to use the test session.
- httpx.AsyncClient is used as the test HTTP client (no real network calls).
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db

# ── In-memory async SQLite engine (no file, no state between tests) ────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a fresh engine + schema for every test function."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Return an AsyncSession bound to the test engine."""
    factory = async_sessionmaker(
        db_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """
    AsyncClient wired to the FastAPI app with get_db() overridden
    so every request goes through the test session.

    follow_redirects=True is required because FastAPI (via Starlette) issues a
    307 redirect for routes registered without a trailing slash when the client
    requests them with one (e.g. /api/stats/ -> /api/stats). Without this the
    stats and sync tests receive a redirect response rather than JSON.
    """
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=True,
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Helper: seed a minimal Movie row directly (bypasses TMDb) ─────────────────
async def create_test_movie(db_session, tmdb_id: int = 550, title: str = "Fight Club"):
    """
    Insert a Movie directly via ORM, using only columns that exist on the model.

    Correct field mapping (conftest vs Movie model):
        original_language  -> language          (the model column is 'language')
        popularity         -> (removed)          (no such column on Movie)
        vote_average       -> tmdb_rating        (the model column is 'tmdb_rating')
        vote_count         -> tmdb_vote_count    (the model column is 'tmdb_vote_count')
    """
    from app.models.movie import Movie
    movie = Movie(
        tmdb_id=tmdb_id,
        title=title,
        year=1999,
        overview="An insomniac office worker forms an underground fight club.",
        poster_path="/poster.jpg",
        backdrop_path="/backdrop.jpg",
        language="en",
        tmdb_rating=8.4,
        tmdb_vote_count=22000,
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie

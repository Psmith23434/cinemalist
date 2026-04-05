# CinemaList — Complete Project Plan & Technical Guide

> **Repository:** [https://github.com/Psmith23434/cinemalist](https://github.com/Psmith23434/cinemalist)
> **Platform Target:** Windows PC (local first) → Fujitsu Futro S740 / VPS → Android Sync
> **Stack:** Python · FastAPI · SQLite → PostgreSQL · React · TMDb API · LLM Integration

---

## Table of Contents

1. [Architecture Recommendation](#1-architecture-recommendation)
2. [Full Tech Stack](#2-full-tech-stack)
3. [Movie API Integration](#3-movie-api-integration)
4. [Feature Plan](#4-feature-plan)
5. [Database Design](#5-database-design)
6. [Sync & Future Android App](#6-sync--future-android-app)
7. [Development Roadmap](#7-development-roadmap)
8. [GitHub & Development Workflow](#8-github--development-workflow)
9. [Local Development Setup (Windows)](#9-local-development-setup-windows)
10. [Best Starting Approach — Summary](#10-best-starting-approach--summary)

---

## 1. Architecture Recommendation

### Option Comparison

| Approach | Pros | Cons | Future-proof? |
|---|---|---|---|
| **Native Python Desktop (Tkinter / PyQt)** | Truly offline, no browser needed | Hard to style, poor mobile story, complex reuse | ❌ Poor |
| **Local Web App — Python backend + browser UI** | Clean UI, reuses backend for Android sync, runs anywhere | Needs a browser open locally | ✅ Excellent |
| **Electron + Python** | Desktop app feel, bundled | Heavy (200MB+), complex setup | ⚠️ Acceptable |

### Recommendation: Local Web App Architecture

Run a **Python backend server** on your PC that your browser connects to via `http://localhost:8000`. This gives you:

- A beautiful, modern UI in the browser (no native GUI limitations)
- The same backend code reused when you move to a VPS or the Fujitsu Futro S740
- A ready-made REST API for Android to sync with later
- No Electron bloat — just Python + a browser you already have

**Architecture diagram:**

```
[Browser / React UI]
         │
         │  HTTP (localhost:8000)
         ▼
[FastAPI Backend — Python]
         │
         ▼
[SQLite Database — local file]
         │
         ▼
[TMDb API — movie metadata]
[Local /media folder — posters]
[LLM Proxy — recommendations & AI features]
```

When you move to a Fujitsu S740 or VPS later:

```
[Android App]   [Browser UI]
       │               │
       └──── HTTPS ────┘
                │
         [Futro S740 / VPS / FastAPI]
                │
         [PostgreSQL]
```

The only things that change during migration are the database (SQLite → PostgreSQL, which SQLAlchemy handles automatically) and the host address. The code stays identical.

---

## 2. Full Tech Stack

### Recommended Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend Framework** | FastAPI (Python 3.11+) | Fast, modern, auto-generates API docs, async support |
| **Database (local)** | SQLite | Zero setup, single file, works perfectly for personal use |
| **Database (VPS later)** | PostgreSQL | Industry standard, free, powerful |
| **ORM** | SQLAlchemy 2.0 + Alembic | Supports both SQLite and PostgreSQL seamlessly |
| **Frontend / UI** | React (Vite) | Component-based, huge ecosystem, pairs well with FastAPI |
| **UI Component Library** | shadcn/ui or Mantine | Beautiful prebuilt components, no design from scratch |
| **Authentication** | FastAPI-Users (optional for v1) | JWT tokens, works locally and on VPS |
| **API Design** | RESTful JSON API | Simple, widely understood, easy for Android to consume |
| **Sync Strategy** | Timestamp + UUID-based sync | Handles conflict detection without a complex CRDT library |
| **Media Storage** | Local `/media/posters/` folder (PC) | Simple, fast; move to S3 or VPS `/media` later |
| **Secrets Management** | `.env` file + `python-dotenv` | Standard practice, never commit API keys |
| **Package Manager** | `pip` + `venv` (beginner friendly) | Built into Python, no extra tools needed |
| **Deployment (local)** | `uvicorn` ASGI server | Comes with FastAPI, simple one-command startup |
| **Deployment (VPS)** | Nginx + `gunicorn` + `uvicorn workers` | Production-ready, standard setup |
| **LLM Integration** | Your existing LLM proxy (GPT/Claude/Gemini) | Recommendations, smart stats, auto-tagging |

### Why FastAPI over Flask or Django?

- **vs Flask:** FastAPI has built-in data validation (Pydantic), async support, and auto-generates Swagger API docs. Flask requires many extra extensions to match this.
- **vs Django:** Django is much heavier and opinionated. FastAPI is lightweight and doesn't force a particular project structure. Django is better for large teams — FastAPI is better for solo projects.

### Why React over plain HTML/Jinja2?

If you used Jinja2 templates (server-rendered HTML), every page would require a full page reload. A React frontend gives you a smooth, app-like experience (instant filtering, no reloads, live search) while still talking to the same FastAPI backend. Vite makes React fast to set up — it starts in under 10 seconds.

If React feels too complex at first, you can start with plain Jinja2 templates and migrate to React later. The backend API won't change.

---

## 3. Movie API Integration

### API Comparison

| API | Free Tier | Data Quality | Rate Limit | Best For |
|---|---|---|---|---|
| **TMDb** ⭐ | Yes (free) | Excellent | ~50 req/s | Full metadata, posters, best choice |
| **OMDb** | 1,000/day free | Good | 1,000/day | Simple lookups, IMDb ratings |
| **Trakt** | Yes | Good | 1,000/5min | Social features, watch history |
| **Open Movie DB** | Free | Medium | Low | Fallback only |

### Recommendation: The Movie Database (TMDb)

**TMDb** is the clear winner for this project:

- Completely **free** with an API key (no credit card required)
- Returns **poster images**, backdrop images, trailers, cast, crew, genres, release dates, runtime, overview, and more
- Supports **multi-language** metadata (German titles/descriptions available)
- Rate limit is ~50 requests/second — essentially unlimited for personal use
- Used by major apps like Plex, Kodi, Letterboxd

**How to get an API key:**
1. Register at [https://www.themoviedb.org](https://www.themoviedb.org)
2. Go to Settings → API → Request an API Key (free account is fine)
3. You receive a `v3 auth key` — store this in your `.env` file

### What Metadata TMDb Returns

```json
{
  "id": 550,
  "title": "Fight Club",
  "original_title": "Fight Club",
  "overview": "A ticking-time-bomb insomniac...",
  "release_date": "1999-10-15",
  "runtime": 139,
  "vote_average": 8.4,
  "vote_count": 26000,
  "genres": [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}],
  "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
  "backdrop_path": "/fCayJrkfRaCRCTh8GqN30f8oyQF.jpg",
  "imdb_id": "tt0137523",
  "spoken_languages": [{"name": "English"}],
  "production_countries": [{"iso_3166_1": "US"}],
  "tagline": "Mischief. Mayhem. Soap."
}
```

Poster image URL: `https://image.tmdb.org/t/p/w500{poster_path}`

### Caching Strategy

You **should** cache movie metadata locally. Here is why and how:

- TMDb data rarely changes — no point re-fetching the same movie every time
- Caching avoids hitting rate limits
- Makes the app work offline for movies you've already added
- Store raw TMDb JSON in a `api_cache` table (see Database Design section)
- Set a cache TTL of 30 days — refresh only if the cached entry is older than 30 days

```python
# Pseudo-code for cache-first fetch
def get_movie_metadata(tmdb_id):
    cached = db.query(ApiCache).filter_by(tmdb_id=tmdb_id).first()
    if cached and (now - cached.fetched_at).days < 30:
        return cached.data_json
    # If not cached or stale, fetch from TMDb
    data = tmdb_api.fetch(tmdb_id)
    db.save(ApiCache(tmdb_id=tmdb_id, data_json=data, fetched_at=now))
    return data
```

### Poster Images

Download and store poster images locally in `/media/posters/{tmdb_id}.jpg`. Do not serve images directly from TMDb in production — download once, store locally, serve from your own app. This makes the app work offline and avoids depending on TMDb's CDN.

---

## 4. Feature Plan

### MVP Features (Phase 1–4)

These are the features you must have before the app is usable:

- Search for movies by title using TMDb
- Add movies to your personal list (auto-populates metadata from TMDb)
- Rate movies (1–10 stars or 0.5 increments)
- Add personal notes/reviews per movie
- Track watch date(s)
- View your movie list with poster images
- Basic filter: by genre, year, rating
- Mark movies as Favourite (heart icon)
- Edit and delete movie entries
- Basic statistics: total watched, average rating, top genres

### Nice-to-Have Features (Phase 5–6)

- **Watchlist** — movies you want to watch but haven't yet
- **Lists / Collections** — custom groupings (e.g., "Nolan Films", "Horror 2024")
- **Custom tags** — e.g., `#rewatched`, `#cinema`, `#drunk-watch`
- **Rewatch tracking** — log the same movie multiple times with different dates/ratings
- **Search history** — recent TMDb searches cached
- **Dark mode** — UI toggle, saved preference
- **Import/Export** — CSV export of your entire list; CSV import for bulk add
- **Duplicate detection** — warn if you try to add a movie already in your list
- **Backup/restore** — one-click SQLite database backup to a `.zip` file
- **Statistics dashboard** — yearly breakdown chart, rating distribution, genre pie chart
- **LLM-powered features** — see Section 5 (AI Integration) below

### Advanced Future Features (Phase 7–8)

- **Android app with sync** — connect to your PC or Fujitsu backend
- **Multi-user support** — separate user accounts with JWT authentication
- **Franchise/collection groups** — e.g., MCU films grouped together (TMDb provides collection data)
- **Letterboxd import** — parse CSV export from Letterboxd into CinemaList
- **Reminders** — "Rewatch this in 6 months" with a notification
- **Social sharing** — share a public profile page showing your top-rated films
- **VPS hosting** — accessible from any device, not just your PC

---

## 5. Database Design

### Schema Overview

The database is split into two logical groups:

**Group A — Your personal data** (stored locally, synced to VPS later):
Movies you've watched, your ratings, notes, lists, tags.

**Group B — TMDb cache** (cached API data):
Raw movie metadata from TMDb. Can be re-fetched anytime — not critical to back up.

---

### Table Definitions

#### `movies` — TMDb movie data (cached locally)

```sql
CREATE TABLE movies (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id        INTEGER UNIQUE NOT NULL,
    imdb_id        TEXT,
    title          TEXT NOT NULL,
    original_title TEXT,
    overview       TEXT,
    release_date   DATE,
    runtime        INTEGER,          -- minutes
    poster_path    TEXT,             -- local file path e.g. /media/posters/550.jpg
    backdrop_path  TEXT,
    vote_average   REAL,             -- TMDb community rating
    tagline        TEXT,
    language       TEXT,             -- original language code e.g. "en"
    tmdb_data_json TEXT,             -- full raw JSON from TMDb (for future fields)
    cached_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `genres`

```sql
CREATE TABLE genres (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id INTEGER UNIQUE,
    name    TEXT NOT NULL
);
```

#### `movie_genres` — many-to-many join

```sql
CREATE TABLE movie_genres (
    movie_id  INTEGER REFERENCES movies(id) ON DELETE CASCADE,
    genre_id  INTEGER REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, genre_id)
);
```

#### `user_movie_entries` — your personal record for each film

This is the most important table. One row per movie you've added to your personal list.

```sql
CREATE TABLE user_movie_entries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid         TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    movie_id     INTEGER NOT NULL REFERENCES movies(id),
    status       TEXT NOT NULL DEFAULT 'watched',
                 -- 'watched' | 'watchlist' | 'dropped' | 'rewatching'
    rating       REAL,            -- your personal rating e.g. 7.5
    is_favorite  BOOLEAN DEFAULT FALSE,
    watch_date   DATE,            -- first watch date
    added_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Sync fields (used later for Android sync):
    sync_version INTEGER DEFAULT 1,
    deleted_at   TIMESTAMP        -- soft delete for sync
);
```

> **Why `uuid`?** When you later sync between PC and Android, you need a globally unique ID that doesn't depend on which device created the record. Auto-increment integers clash between devices (PC creates entry #1, Android also creates entry #1). UUIDs are unique everywhere.

#### `watch_history` — tracks every time you've watched a film

```sql
CREATE TABLE watch_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id   INTEGER NOT NULL REFERENCES user_movie_entries(id) ON DELETE CASCADE,
    watched_on DATE NOT NULL,
    notes      TEXT,           -- notes specific to this viewing
    platform   TEXT,           -- e.g. "Netflix", "Cinema", "Blu-ray"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `notes` — personal notes and reviews

```sql
CREATE TABLE notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id   INTEGER NOT NULL REFERENCES user_movie_entries(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    is_review  BOOLEAN DEFAULT FALSE,   -- true = main review, false = quick note
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `lists` — custom collections

```sql
CREATE TABLE lists (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid           TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    name           TEXT NOT NULL,
    description    TEXT,
    is_public      BOOLEAN DEFAULT FALSE,
    cover_movie_id INTEGER REFERENCES movies(id),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `list_entries` — movies inside a list

```sql
CREATE TABLE list_entries (
    list_id    INTEGER REFERENCES lists(id) ON DELETE CASCADE,
    entry_id   INTEGER REFERENCES user_movie_entries(id) ON DELETE CASCADE,
    position   INTEGER,          -- ordering within the list
    added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (list_id, entry_id)
);
```

#### `tags`

```sql
CREATE TABLE tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL    -- e.g. "#rewatched", "#cinema"
);
```

#### `entry_tags` — many-to-many join

```sql
CREATE TABLE entry_tags (
    entry_id INTEGER REFERENCES user_movie_entries(id) ON DELETE CASCADE,
    tag_id   INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (entry_id, tag_id)
);
```

#### `api_cache` — raw TMDb responses

```sql
CREATE TABLE api_cache (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key  TEXT UNIQUE NOT NULL,  -- e.g. "tmdb_search_fight+club"
    data_json  TEXT NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP              -- set to fetched_at + 30 days
);
```

#### `llm_cache` — cached LLM recommendation results

```sql
CREATE TABLE llm_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    library_hash    TEXT UNIQUE NOT NULL,  -- hash of watched movies list
    prompt_used     TEXT NOT NULL,         -- the exact prompt sent to the LLM
    response_json   TEXT NOT NULL,         -- the raw JSON response from the LLM
    model_used      TEXT,                  -- e.g. "gpt-4o-mini", "claude-3-haiku"
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

> **Why cache LLM responses?** The recommendations only need to refresh when your library changes. Caching avoids calling the LLM repeatedly for the same data, keeping costs near zero.

#### `sync_log` — for future Android sync tracking

```sql
CREATE TABLE sync_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id    TEXT NOT NULL,      -- which device created this change
    table_name   TEXT NOT NULL,      -- "user_movie_entries", "notes", etc.
    record_uuid  TEXT NOT NULL,      -- uuid of the changed record
    action       TEXT NOT NULL,      -- "create", "update", "delete"
    synced_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload_json TEXT                -- snapshot of the change
);
```

### Entity Relationships

```
movies ──< movie_genres >── genres

movies ──< user_movie_entries ──< watch_history
                     │
                     ├──< notes
                     ├──< entry_tags >── tags
                     └──< list_entries >── lists
```

### What to Store Locally vs. Fetch from API

| Data Type | Store Locally | Re-fetch from API |
|---|---|---|
| Your ratings, notes, lists | ✅ Always | ❌ Never |
| Watch dates, favourites | ✅ Always | ❌ Never |
| Movie title, year, genre | ✅ Cache locally | ✅ After 30 days |
| Poster images | ✅ Download once | ✅ If file missing |
| Raw TMDb JSON | ✅ Cache in `api_cache` | ✅ After 30 days |
| TMDb community ratings | ✅ Cache | ✅ Refresh weekly |
| Search results | ✅ Cache 1 hour | ✅ After TTL |
| LLM recommendations | ✅ Cache in `llm_cache` | ✅ When library changes |

---

## 6. Sync & Future Android App

### Preparing for Sync from Day One

The most important design decisions to make **now** (before writing any code) that will make Android sync possible later:

1. **Add `uuid` fields** to every user-owned table (`user_movie_entries`, `lists`, `notes`). Do this in your initial schema — adding UUIDs later requires a database migration.
2. **Add `updated_at` timestamps** to every table. This is how you detect what changed since the last sync.
3. **Use soft deletes** — add a `deleted_at` column instead of hard-deleting rows. When Android deletes an entry, the PC needs to know it was deleted (not just missing). A hard delete leaves no trace.
4. **Build REST API endpoints from Phase 1** — even if Android doesn't exist yet, having an API means you can test sync logic early.

### How Sync Will Work (Timestamp-Based)

This is a simple and reliable sync strategy for a personal app:

```
Android App                         PC / Server
    │                                    │
    │── GET /api/sync?since=2024-01-01 ──►│
    │                                    │ Returns all records updated
    │◄── { entries: [...], lists: [...] }─│ after the given timestamp
    │                                    │
    │── POST /api/sync/push ─────────────►│
    │   { entries: [new/changed ones] }  │ PC merges incoming changes
    │◄── { ok: true } ───────────────────│
```

**Step by step:**
1. Android stores `last_sync_at` timestamp locally
2. On sync, it sends `GET /sync?since={last_sync_at}` — server returns everything changed since then
3. Android applies the changes to its local SQLite
4. Android sends its own local changes to `POST /sync/push`
5. Update `last_sync_at` to now

### Conflict Resolution Strategy

For a personal single-user app, keep conflict resolution simple:

- **"Last write wins"** — if both PC and Android edited the same entry, the one with the newer `updated_at` wins
- For ratings and notes, this is acceptable for personal use
- Log all conflicts in `sync_log` so you can inspect them if something seems wrong

### Offline Support

Both the PC app (browser) and Android app should work offline:

- **PC app:** Already works offline — SQLite is local, no internet required except for TMDb searches
- **Android app:** Uses its own local SQLite database, syncs when internet is available
- Design rule: **never block UI on sync** — sync runs in the background, app is always usable

### User Accounts

| Phase | Auth Approach |
|---|---|
| Phase 1 (local PC) | No authentication needed — only you have access |
| Phase 2 (VPS) | Add JWT authentication via FastAPI-Users |
| Phase 3 (Android) | Android stores JWT token, login screen added |

### What Changes When Moving to VPS / Fujitsu S740

| Component | Local PC | Futro S740 / VPS |
|---|---|---|
| Database | SQLite file | SQLite (Futro) or PostgreSQL (VPS) |
| Media storage | `/media/posters/` local folder | Same path on new machine |
| Server | `uvicorn` dev server | `gunicorn` + `nginx` reverse proxy |
| Domain | `localhost:8000` | Local IP or `https://yourdomain.com` |
| HTTPS | Not needed locally | Required for outside access |
| Authentication | Optional | Required for outside access |
| Migration effort | — | ~1 evening: copy DB + posters, change IP in Android |

SQLAlchemy handles the SQLite → PostgreSQL switch automatically — you only change the `DATABASE_URL` in your `.env` file. The Python code stays the same.

---

## 7. Development Roadmap

### Phase 1 — Planning & Repository Setup ✅ Done

**Goals:**
- Set up Python environment, project structure, and Git
- Configure repository with a clear folder layout
- Add `.gitignore`, `.env.example`, and initial `README.md`

**Deliverables:**
- Working Python virtual environment
- Folder structure committed to GitHub
- `.env` file with `TMDB_API_KEY` placeholder

**Folder Structure:**

```
cinemalist/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               ← FastAPI app entry point
│   │   ├── config.py             ← settings, reads from .env
│   │   ├── database.py           ← SQLAlchemy engine + session
│   │   ├── models/
│   │   │   ├── movie.py
│   │   │   ├── entry.py
│   │   │   ├── list.py
│   │   │   └── tag.py
│   │   ├── schemas/              ← Pydantic request/response schemas
│   │   │   ├── movie.py
│   │   │   └── entry.py
│   │   ├── routers/              ← API route handlers
│   │   │   ├── movies.py
│   │   │   ├── entries.py
│   │   │   ├── lists.py
│   │   │   ├── search.py
│   │   │   ├── stats.py
│   │   │   └── ai.py             ← LLM-powered endpoints
│   │   └── services/             ← business logic
│   │       ├── tmdb.py           ← TMDb API integration
│   │       ├── llm.py            ← LLM proxy integration
│   │       └── sync.py           ← sync logic
│   ├── migrations/               ← Alembic migration files
│   ├── media/
│   │   └── posters/              ← downloaded poster images
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/                  ← API client (fetch wrappers)
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

**Risks:**
- Environment misconfiguration — mitigated by `.env.example` and clear setup docs

---

### Phase 2 — Backend & Database 🔧 In Progress

**Goals:**
- Implement all SQLAlchemy models
- Set up Alembic for database migrations
- Build CRUD API endpoints for movies and entries
- Configure FastAPI with CORS

**Deliverables:**
- Running FastAPI server at `http://localhost:8000`
- Auto-generated API docs at `http://localhost:8000/docs`
- All database tables created via Alembic migration
- Endpoints: `GET/POST/PUT/DELETE` for movies, entries, lists, tags, notes

**Key commands:**
```bash
# Initialize Alembic
alembic init migrations

# Create a migration after adding/changing models
alembic revision --autogenerate -m "initial tables"

# Apply migrations
alembic upgrade head
```

**Risks:**
- Schema design mistakes — use the design in Section 5 as your blueprint and add UUIDs from the start

---

### Phase 3 — TMDb API Integration

**Goals:**
- Implement TMDb search and movie detail fetching
- Download and store poster images locally
- Build cache layer (check `api_cache` before calling TMDb)

**Deliverables:**
- `GET /api/search?q=fight+club` endpoint that searches TMDb
- `POST /api/movies/import/{tmdb_id}` that saves a movie to the local database
- Poster images downloaded to `/media/posters/{tmdb_id}.jpg`
- Cache layer with 30-day TTL

**Example `.env` setup:**
```ini
TMDB_API_KEY=your_key_here
TMDB_BASE_URL=https://api.themoviedb.org/3
TMDB_IMAGE_BASE=https://image.tmdb.org/t/p/w500
DATABASE_URL=sqlite:///./cinemalist.db
MEDIA_DIR=./media
```

**Risks:**
- TMDb API key not working — test immediately after getting the key
- Image download failures — add retry logic and a fallback placeholder poster

---

### Phase 4 — Frontend / UI

**Goals:**
- Set up React + Vite project in the `frontend/` folder
- Build the main pages: Movie List, Movie Detail, Add Movie, Statistics, Lists
- Connect all pages to the FastAPI backend
- Implement search-as-you-type for TMDb movie search

**Deliverables:**
- Fully functional browser UI running at `http://localhost:5173`
- Movie grid view with poster images
- Movie detail page with rating slider, notes editor, watch date picker
- Statistics page with charts (Recharts)
- Dark mode toggle

**CORS setup for FastAPI:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Risks:**
- React learning curve — start with simple pages before adding complex state management
- CORS errors between Vite (port 5173) and FastAPI (port 8000) — see above fix

---

### Phase 5 — Testing, Polish & AI Integration

**Goals:**
- Write basic tests for the most important backend logic
- Fix edge cases: missing posters, duplicate movies, empty states
- Performance: add database indexes on frequently queried columns
- Integrate LLM proxy for AI-powered features

**Deliverables:**
- `pytest` test suite for backend (`backend/tests/`)
- Database indexes added on key columns
- Error handling for API failures
- Friendly error messages in the UI
- LLM-powered recommendation endpoint
- Narrative statistics report
- Auto-tagging suggestions

**Add these indexes in Alembic:**
```python
op.create_index('ix_entries_updated_at', 'user_movie_entries', ['updated_at'])
op.create_index('ix_movies_tmdb_id', 'movies', ['tmdb_id'])
```

---

#### AI Integration (Phase 5) — LLM-Powered Features

You have access to a proxy that supports multiple LLM models (GPT, Claude, Gemini). This is integrated into a new `services/llm.py` service and a new `routers/ai.py` router.

##### How It Works

The LLM does **not** need internet access. It already knows millions of films from its training data. TMDb handles all real-time movie lookups. The two systems work together like this:

```
Step 1: FastAPI reads your watch history from SQLite
Step 2: Builds a compact prompt from your top-rated movies
Step 3: Sends prompt to LLM via your proxy
Step 4: LLM returns 5-10 movie title suggestions
Step 5: FastAPI fetches full metadata + posters for each via TMDb
Step 6: React UI displays rich movie cards with reasons
```

##### New `.env` variables required

```ini
LLM_PROXY_URL=https://your-proxy-url/v1/chat/completions
LLM_API_KEY=your_proxy_api_key
LLM_MODEL=gpt-4o-mini         # or claude-3-haiku, gemini-1.5-flash, etc.
```

##### Feature 1 — Personalized Recommendations

**Endpoint:** `GET /api/v1/ai/recommend`

**System prompt (static, sent once per request):**
```
You are a personal movie advisor with deep knowledge of world cinema.
The user will provide their watch history with personal ratings (1-10).
Recommend exactly 8 movies they have NOT seen.

Return ONLY valid JSON in this exact format, no extra text:
[
  {
    "title": "Movie Title",
    "year": 2019,
    "reason": "A detailed explanation of why this specific film suits
               this user's taste, referencing their watched films,
               preferred directors, themes, or genres they enjoy."
  }
]

Rules:
- Each reason should be 2-4 sentences, specific and personal
- Reference actual films from their history when explaining why
- Vary the recommendations across genres unless history shows overwhelming preference
- Never include films already in their watched list or watchlist
- Prioritize lesser-known gems alongside well-known titles
```

**User prompt (dynamic, built from DB — ~50-80 tokens):**
```python
def build_recommendation_prompt(movies: list) -> str:
    top_rated   = sorted(movies, key=lambda m: m.rating or 0, reverse=True)
    liked       = [f"{m.title} ({m.rating}/10)" for m in top_rated if (m.rating or 0) >= 7][:12]
    disliked    = [f"{m.title} ({m.rating}/10)" for m in top_rated if (m.rating or 0) <= 5][:5]
    top_genres  = get_top_genres(movies, limit=4)
    fav_titles  = [m.title for m in movies if m.is_favorite][:5]

    parts = [f"Highly rated: {', '.join(liked)}"]
    if disliked:
        parts.append(f"Disliked: {', '.join(disliked)}")
    if fav_titles:
        parts.append(f"Favourites: {', '.join(fav_titles)}")
    parts.append(f"Top genres: {', '.join(top_genres)}")
    parts.append(f"Total watched: {len(movies)} films")
    return "\n".join(parts)
```

**Example prompt sent to LLM:**
```
Highly rated: Interstellar (9/10), Arrival (9/10), Dune (8.5/10),
              Blade Runner 2049 (8/10), The Prestige (8/10), Heat (7.5/10)
Disliked: Transformers (3/10), Fast X (4/10)
Favourites: Interstellar, Arrival, Dune
Top genres: Sci-Fi, Thriller, Drama, Crime
Total watched: 183 films
```

**Example LLM response:**
```json
[
  {
    "title": "Annihilation",
    "year": 2018,
    "reason": "Alex Garland directed Ex Machina, which shares Arrival's
               theme of encountering the unknowable. Annihilation has the
               same slow-burn tension and ambiguous ending you seem to love.
               Visually striking, philosophically unsettling."
  },
  {
    "title": "Coherence",
    "year": 2013,
    "reason": "A micro-budget sci-fi thriller that rewards the same kind
               of careful attention you give to films like The Prestige.
               Built on a single clever idea and executed with remarkable
               tension. One of the most underrated sci-fi films of the decade."
  }
]
```

**Cost estimate:**
| Component | Tokens | Cost (GPT-4o-mini) |
|---|---|---|
| System prompt | ~120 | — |
| User prompt | ~80 | — |
| LLM response (8 films) | ~400 | — |
| **Total** | **~600 tokens** | **~€0.0001 per request** |

At this cost, clicking "Recommend" 1,000 times costs less than **€0.10 total**.

---

##### Feature 2 — Narrative Statistics Report

**Endpoint:** `GET /api/v1/ai/stats-report`

The basic stats page shows numbers. This feature turns those numbers into a readable personal story about your viewing habits.

**System prompt:**
```
You are a film critic writing a short personal report about someone's
movie-watching year. Write in a warm, insightful tone — like a thoughtful
friend who also loves cinema. Be specific, not generic.

The user will provide their annual statistics. Write 3-4 paragraphs
covering: overall activity, taste patterns, most interesting discoveries,
and one forward-looking observation. Do not use bullet points.
```

**User prompt (built from DB stats):**
```
Year: 2024
Total watched: 63 films
Average rating: 7.2/10
Top genres: Sci-Fi (18), Thriller (14), Drama (11)
Highest rated: Dune Part Two (9.5), Poor Things (9), Zone of Interest (8.5)
Lowest rated: Aquaman 2 (3), Madame Web (2.5)
New directors discovered: Yorgos Lanthimos, Jonathan Glazer
Rewatch count: 4
Most active month: March (11 films)
```

---

##### Feature 3 — Auto-Tag Suggestions

**Endpoint:** `POST /api/v1/ai/suggest-tags`

When you add a new movie, the LLM reads the TMDb overview and suggests relevant personal tags.

**System prompt:**
```
You are a movie tagging assistant. Based on a film's description,
suggest 3-5 short personal tags a viewer might use to categorize it.
Tags should be practical and personal, not just genre labels.

Return ONLY a JSON array of strings. Examples of good tags:
"#mindfuck", "#slow-burn", "#based-on-true-story", "#feel-good",
"#rewatch-worthy", "#disturbing", "#visually-stunning", "#cult-classic"
```

**User prompt:**
```
Title: Parasite (2019)
Overview: Greed and class discrimination threaten the newly formed
symbiotic relationship between the wealthy Park family and the
destitute Kim clan.
Genres: Drama, Thriller, Comedy
```

**LLM response:**
```json
["#class-commentary", "#slow-burn", "#plot-twist", "#rewatch-worthy", "#foreign-language"]
```

---

##### Feature 4 — Natural Language Search

**Endpoint:** `GET /api/v1/ai/search?q=that+french+heist+movie+I+liked`

Lets you describe a movie vaguely and the LLM matches it against your library.

**System prompt:**
```
You are a movie search assistant. The user will describe a movie
vaguely. Given a list of movies in their library, identify the most
likely match. Return only the tmdb_id of the best match, or null
if no match found. Return ONLY valid JSON: {"tmdb_id": 123} or {"tmdb_id": null}
```

---

##### Caching Strategy for LLM Calls

LLM calls are cached in the `llm_cache` table to avoid redundant API calls:

```python
import hashlib, json

def get_recommendations(db, movies):
    # Build a fingerprint of the current library state
    library_hash = hashlib.md5(
        json.dumps([(m.tmdb_id, m.rating) for m in sorted(movies, key=lambda x: x.tmdb_id)])
        .encode()
    ).hexdigest()

    # Return cached result if library hasn't changed
    cached = db.query(LlmCache).filter_by(library_hash=library_hash).first()
    if cached:
        return json.loads(cached.response_json)

    # Otherwise call the LLM and cache the result
    prompt  = build_recommendation_prompt(movies)
    result  = call_llm(prompt)
    db.add(LlmCache(library_hash=library_hash, prompt_used=prompt,
                    response_json=json.dumps(result), model_used=LLM_MODEL))
    db.commit()
    return result
```

This means in practice the LLM is only called when you add or rate a new movie — not on every page visit.

---

##### UI Integration

The React frontend gets a new **"For You"** tab on the Statistics page:

```
[ Overview ] [ Charts ] [ For You ✨ ]
                                  │
                     ┌────────────▼────────────┐
                     │  🎬 Recommended For You  │
                     │  Based on 183 films      │
                     │                          │
                     │  [Poster] Annihilation   │
                     │  2018 · Sci-Fi · A24     │
                     │  "Because you gave       │
                     │  Arrival 9/10..."        │
                     │                          │
                     │  [Poster] Coherence      │
                     │  ...                     │
                     │                          │
                     │  [ Refresh suggestions ] │
                     └──────────────────────────┘
```

**Risks:**
- Skipping tests — at minimum, test the TMDb integration and sync endpoints
- LLM proxy downtime — add a graceful fallback (hide AI features if proxy unreachable)
- LLM hallucinating wrong movie years — always verify title + year against TMDb after receiving suggestions

---

### Phase 6 — Local Deployment (Windows PC)

**Goals:**
- Make it easy to start the app with a single double-click
- Document the startup process

**Deliverables:**
- `start.bat` script that starts the backend server
- React frontend built to `backend/static/` so FastAPI serves both

**`start.bat` example:**
```batch
@echo off
cd backend
call venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Serve frontend from FastAPI directly:**
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

**Risks:**
- Windows firewall blocking port 8000 — run as administrator once to allow it

---

### Phase 7 — Futro S740 / VPS Migration

**Goals:**
- Set up Ubuntu 22.04 on the Fujitsu Futro S740 (or a Linux VPS)
- Switch database from SQLite to PostgreSQL (optional — SQLite works fine on Futro for personal use)
- Configure Nginx as reverse proxy
- Add HTTPS via Let's Encrypt if accessing from outside home network

**Deliverables:**
- Running server on Futro S740 at a fixed local IP (e.g. `192.168.1.100:8000`)
- Optional: DuckDNS free domain for outside-home access
- Optional: PostgreSQL + data migrated from SQLite
- Systemd service to auto-start app on Futro boot

**Migration steps (approx. 1 evening):**
1. Install Ubuntu Server 22.04 on Futro S740
2. `scp` the project folder from Windows PC to Futro
3. `pg_dump` + `pg_restore` if switching to PostgreSQL (optional)
4. Set Futro to a static local IP in your router
5. Update one line in Android app: server address from `localhost` to `192.168.1.100`

**VPS alternative:** Hetzner CX22 (~€4/month, Germany) if you want 24/7 outside access without port forwarding.

**Risks:**
- Database migration data loss — always take a full SQLite backup before migrating

---

### Phase 8 — Android Sync Support

**Goals:**
- Build sync endpoints in FastAPI
- Build Android app in React Native (Expo)
- Implement offline-first local SQLite on Android
- Background sync when connected to internet

**Deliverables:**
- Sync API endpoints tested and documented
- Android app with local database that syncs with the backend
- Login screen (JWT authentication)
- All MVP features working on Android

**Sync endpoint design:**
```
GET  /api/v1/sync?since=2025-01-01T00:00:00Z
     → Returns entries, lists, notes updated after `since`

POST /api/v1/sync/push
     Body: { entries: [...], lists: [...], deleted: [...] }
     → Server merges changes, returns conflicts (if any)
```

**Android technology recommendation:** Use **React Native + Expo** — reuses your JavaScript/React knowledge from the frontend, faster development, easier setup.

**Risks:**
- Sync conflicts — document the "last write wins" strategy, warn users when conflicts occur
- Android SQLite schema must exactly match backend schema — share a schema definition file

---

## 8. GitHub & Development Workflow

### Is the Repo Workflow Practical?

Yes. The repository at [https://github.com/Psmith23434/cinemalist](https://github.com/Psmith23434/cinemalist) currently has a README, project plan, and placeholder files. The plan is to build on this foundation properly with the full Python stack.

### Can an AI Assistant Commit to Your Repo?

Yes — an AI assistant with GitHub API access can:
- Read files, create new files, update existing files, create branches, and open pull requests
- The AI never runs code on your machine — it only pushes changes to the remote repository
- You then `git pull` on your PC to get the changes

**Safe workflow:**
1. AI creates a feature branch (e.g., `phase-2/backend`)
2. AI pushes code to that branch
3. You review the code on GitHub (Files Changed tab in the Pull Request)
4. If happy, you merge the pull request
5. You run `git pull` on your PC to update your local copy

### What You Need on Your PC

**Required (lightweight, ~260MB total):**
- Git for Windows: https://git-scm.com/download/win (~50MB)
- Python 3.11+: https://python.org (~30MB)
- Node.js 20+ (for React frontend): https://nodejs.org (~80MB)
- VS Code: https://code.visualstudio.com (~100MB)

**Not required:**
- Docker (optional, not needed for local development)
- Any database installer (SQLite is a single file, built into Python)
- Any web server (FastAPI runs its own via `uvicorn`)

### Recommended Git Branching Strategy

Use a simple two-branch strategy (suitable for solo projects):

```
main          ← stable, always works, never commit directly
  └─ phase-2/backend
  └─ phase-3/tmdb-integration
  └─ phase-4/frontend
  └─ phase-5/ai-integration
  └─ fix/poster-download-error
```

**Workflow:**
```bash
# Get latest from main
git checkout main
git pull origin main

# Start a new phase/feature
git checkout -b phase-2/backend

# Work, commit often
git add .
git commit -m "feat: add SQLAlchemy models"

# Push to GitHub
git push origin phase-2/backend

# On GitHub: open a Pull Request → review → merge to main
# On PC:
git checkout main
git pull origin main
```

### Reviewing AI-Generated Code Before Using It

1. Go to `github.com/Psmith23434/cinemalist/pulls` — open the AI-created pull request
2. Click the **Files Changed** tab — every added/changed/removed line is shown
3. Read through the diff — look for hardcoded secrets, wrong logic, missing error handling
4. Leave comments on specific lines if you have questions
5. Click **Merge pull request** only when satisfied

---

## 9. Local Development Setup (Windows)

### Step-by-Step Setup Checklist

#### Step 1 — Install Prerequisites

- [ ] Install Python 3.11+: https://python.org/downloads
  - During install, **check the box "Add Python to PATH"**
- [ ] Install Git: https://git-scm.com/download/win
- [ ] Install Node.js 20 LTS: https://nodejs.org
- [ ] Install VS Code: https://code.visualstudio.com

#### Step 2 — Clone the Repository

```bash
git clone https://github.com/Psmith23434/cinemalist.git
cd cinemalist
```

#### Step 3 — Set Up Python Virtual Environment

```bash
cd backend
python -m venv venv

# Activate (Windows):
venv\Scripts\activate
# You should see (venv) in your terminal
```

#### Step 4 — Install Python Packages

```bash
pip install fastapi uvicorn sqlalchemy alembic python-dotenv httpx pillow pytest
pip freeze > requirements.txt
```

#### Step 5 — Set Up Environment Variables

Create `backend/.env` (never commit this to Git):

```ini
TMDB_API_KEY=your_tmdb_api_key_here
DATABASE_URL=sqlite:///./cinemalist.db
MEDIA_DIR=./media
SECRET_KEY=change_this_to_a_random_string_later
DEBUG=True

# LLM Proxy (add when reaching Phase 5)
LLM_PROXY_URL=https://your-proxy-url/v1/chat/completions
LLM_API_KEY=your_proxy_api_key
LLM_MODEL=gpt-4o-mini
```

Add to `.gitignore`:
```
.env
__pycache__/
*.pyc
venv/
*.db
media/posters/
```

Also create `backend/.env.example` (safe to commit — no real values):
```ini
TMDB_API_KEY=your_tmdb_api_key_here
DATABASE_URL=sqlite:///./cinemalist.db
MEDIA_DIR=./media
SECRET_KEY=generate_a_random_string
DEBUG=True
LLM_PROXY_URL=https://your-proxy-url/v1/chat/completions
LLM_API_KEY=your_proxy_api_key
LLM_MODEL=gpt-4o-mini
```

#### Step 6 — Run Database Migrations

```bash
alembic upgrade head
```

#### Step 7 — Start the Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Visit `http://localhost:8000/docs` — Swagger API documentation.

#### Step 8 — Set Up the Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Visit `http://localhost:5173` — React app is running.

### Do You Need Docker?

**No — Docker is completely optional at this stage.** Skip it for now and add it in Phase 7 (Futro/VPS deployment) if needed. For local development on your own PC with SQLite, Docker adds complexity without any benefit.

---

## 10. Best Starting Approach — Summary

### Recommended Architecture
**Local Web App** — FastAPI backend + React frontend, running on your PC, accessible at `localhost:8000`.

### Recommended Stack at a Glance

| Layer | Choice |
|---|---|
| Backend | Python 3.11 + FastAPI + SQLAlchemy + Alembic |
| Database | SQLite (local) → PostgreSQL (VPS later, optional on Futro) |
| Frontend | React + Vite + Mantine UI |
| Movie API | TMDb (free, best quality) |
| AI Features | LLM proxy (GPT/Claude/Gemini) — Phase 5 |
| Sync | UUID primary keys + `updated_at` timestamps from day one |
| Future server | Fujitsu Futro S740 (Ubuntu) — own hardware, ~€0/month |

### Day 1 Action List

1. **Clone the repo:** `git clone https://github.com/Psmith23434/cinemalist.git`
2. **Register on TMDb** and get your free API key: https://www.themoviedb.org/settings/api
3. **Create the folder structure** described in Phase 1
4. **Create `.env`** with your TMDb key and `DATABASE_URL=sqlite:///./cinemalist.db`
5. **Create the database models** using the schema in Section 5 — start with `movies` and `user_movie_entries`
6. **Test the TMDb search** — make one API call manually in Python before building anything else
7. **Build upward from there** — backend endpoints first, then UI, then AI features in Phase 5

### The Most Important Principle

> **Build the REST API correctly from Phase 1, even if there is no Android app yet.**

Having a proper REST API (`GET /api/movies`, `POST /api/entries`, etc.) costs almost nothing extra now, and saves a massive amount of rework later when you want to add Android sync. The API is also how the React frontend talks to the backend — you need it regardless.

---

*Document generated for the CinemaList project — [github.com/Psmith23434/cinemalist](https://github.com/Psmith23434/cinemalist)*

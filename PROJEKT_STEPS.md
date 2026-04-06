# CinemaList — Project Steps

> Last updated: 2026-04-06 13:20 CEST
> **Legend:** ✅ Done · 🔶 In Progress · ⏳ Up Next · 🔲 Planned · 🚫 N/A (won't do)

---

## Phase 1 — Planning & Repository Setup ✅ DONE

| # | Task | Status | Evidence |
|---|---|---|---|
| 1.1 | Create GitHub repository | ✅ | `github.com/Psmith23434/cinemalist` |
| 1.2 | Define full project plan (`PROJECT_PLAN.md`) | ✅ | `/PROJECT_PLAN.md` (45 KB) |
| 1.3 | Set up folder structure (`backend/`, etc.) | ✅ | `backend/app/`, `backend/alembic/` |
| 1.4 | Add `.gitignore`, `.env.example`, `README.md` | ✅ | `/README.md`, `backend/.env.example` |
| 1.5 | Choose tech stack (FastAPI + SQLite + React + TMDb) | ✅ | Documented in `PROJECT_PLAN.md` |
| 1.6 | Define database schema (all 11 tables) | ✅ | ORM models + migration |
| 1.7 | Define API design & sync strategy | ✅ | Documented in `PROJECT_PLAN.md` |

---

## Phase 2 — Backend & Database ✅ DONE

| # | Task | Status | Evidence |
|---|---|---|---|
| 2.1 | Set up Python virtual environment + `requirements.txt` | ✅ | `backend/requirements.txt` |
| 2.2 | Create FastAPI app entry point (`app/main.py`) | ✅ | `backend/app/main.py` |
| 2.3 | Configure SQLAlchemy + Alembic (`database.py`, `alembic.ini`) | ✅ | `backend/alembic.ini`, `backend/app/core/` |
| 2.4 | Write all SQLAlchemy ORM models | ✅ | `backend/app/models/` |
| | → `movies`, `genres`, `movie_genres` | ✅ | |
| | → `entries`, `watch_events` | ✅ | |
| | → `tags`, `entry_tags` | ✅ | |
| | → `lists`, `list_items` | ✅ | |
| | → `tmdb_cache`, `sync_log` | ✅ | |
| 2.5 | Write Alembic migration (`0001_initial_tables.py`) | ✅ | `backend/alembic/versions/0001_initial_tables.py` |
| 2.6 | Apply migration → `cinemalist.db` created locally | ✅ | Applied via `launcher.py` → Start Backend |
| 2.7 | Build `run.py` helper script | ✅ | `backend/run.py` |
| 2.8 | Build GUI launcher (`launcher.py`) — Backend + Frontend | ✅ | `/launcher.py` |
| 2.9 | Add `start.bat` one-click startup script | ✅ | `/start.bat` |

> **How to start (dev mode):** `python launcher.py` → **▶ Start Backend** (alembic + uvicorn :8000) → **▶ Start Frontend** (Vite dev :5173).
> **How to start (production):** `python launcher.py` → **▶ Build & Serve** (builds React → `backend/static/`) → **▶ Start Backend** → open `http://localhost:8000`.

---

## Phase 3 — TMDb API Integration ✅ DONE

| # | Task | Status | Evidence |
|---|---|---|---|
| 3.1 | Create `app/services/tmdb.py` — search, detail, import | ✅ | `backend/app/services/tmdb.py` |
| 3.2 | Implement cache-first logic (7-day TTL in `tmdb_cache`) | ✅ | Inside `tmdb.py` |
| 3.3 | ~~Download + store poster images to `media/posters/`~~ | 🚫 | **Won't do.** Posters via TMDb CDN. |
| 3.4 | Write Pydantic schemas | ✅ | `schemas/movie.py`, `schemas/entry.py`, `schemas/stats.py`, `schemas/list.py` |
| 3.5 | Build API router: `GET /api/search/tmdb?q=` | ✅ | `backend/app/api/search.py` |
| 3.6 | Build API router: `POST /api/search/tmdb/import/{tmdb_id}` | ✅ | `backend/app/api/search.py` |
| 3.7 | Build API router: `GET /api/movies/` | ✅ | `backend/app/api/movies.py` |
| 3.8 | Build CRUD for entries | ✅ | `backend/app/api/entries.py` |
| 3.9 | Build API routers: genres, tags, lists, stats, sync | ✅ | |
| 3.10 | Smoke-test all endpoints in Swagger UI (`/docs`) | ✅ | All passed (2026-04-06) |

---

## Phase 4 — React Frontend / UI ✅ DONE

| # | Task | Status |
|---|---|---|
| 4.1 | Set up React + Vite project in `frontend/` | ✅ |
| 4.2 | Install Mantine UI v7 + `@mantine/dates@7` | ✅ |
| 4.3 | Build Movie Grid / Library page (poster cards) | ✅ |
| 4.4 | Build Movie Search page (live TMDb search-as-you-type) | ✅ |
| 4.5 | Build Movie Detail page (rating, notes, watch date) | ✅ |
| 4.6 | Build Statistics page (totals, avg rating, genre breakdown) | ✅ |
| 4.7 | Build Lists & Tags management | ✅ |
| 4.8 | Add dark mode toggle | ✅ |
| 4.9 | Configure CORS between Vite (5173) and FastAPI (8000) | ✅ |
| 4.10 | Wire frontend to live backend | ✅ |
| 4.11 | Build React frontend as production bundle into `backend/static/` | ✅ |

### 4.11 — Production Build Setup (Completed 2026-04-06)

| What | Detail |
|---|---|
| `vite.config.js` | `base: '/'`, `outDir: '../backend/static'`, `emptyOutDir: true` |
| `backend/app/main.py` | Mounts `/assets` from `backend/static/assets`; SPA catch-all `GET /{full_path:path}` returns `index.html` so React Router works on hard refresh |
| `launcher.py` | New gold **▶ Build & Serve** button runs `npm run build`, streams output to log, updates prod-ready label, opens `:8000` on success |
| **To build manually** | `cd frontend && npm run build` — output lands in `backend/static/` automatically |

### 4.10 Frontend Bug Fixes (2026-04-06)

| # | File | Fix |
|---|---|---|
| F1 | `MovieDetailPage.jsx` | `is_favourite` → `is_favorite`; `watched_on` → `first_watched_at` |
| F2 | `MovieDetailPage.jsx` | Watch history dates → human-readable `DD MMM YYYY` |
| F3 | `FavouritesPage.jsx` | `favourites: true` → `is_favorite: true`; `limit` → `per_page` |
| F4 | `WatchlistPage.jsx` | `watchlist: true` → `is_watchlisted: true`; `limit` → `per_page` |
| F5 | `LibraryPage.jsx` | `is_favorite` fix; `per_page` fix; client-side sort fixed |
| F6 | `App.jsx` + `ListDetailPage.jsx` | Added `/lists/:id` route + full list detail page |
| F7 | `AddMoviePage.jsx` | Duplicate detection: 409 → navigate to existing entry |

---

## Phase 5 — Testing, Polish & AI Integration 🔶 IN PROGRESS

| # | Task | Status |
|---|---|---|
| 5.1 | Write `pytest` test suite for backend (`backend/tests/`) | ✅ |
| 5.2 | Add database indexes on frequently queried columns | 🔲 |
| 5.3 | Add error handling: missing posters, API failures, duplicates | 🔲 |
| 5.4 | Implement `app/services/llm.py` — LLM proxy connection | ⏳ |
| 5.5 | Build `GET /api/ai/recommend` — personalised recommendations | 🔲 |
| 5.6 | Build `GET /api/ai/stats-report` — narrative stats summary | 🔲 |
| 5.7 | Build `POST /api/ai/suggest-tags` — auto-tag suggestions | 🔲 |
| 5.8 | Build `GET /api/ai/search` — natural language library search | 🔲 |
| 5.9 | Add LLM response caching (`llm_cache` table) | 🔲 |
| 5.10 | Add "For You ✨" tab in React Statistics page | 🔲 |

### 5.1 — Test Suite Details (Completed 2026-04-06)

| File | Coverage |
|---|---|
| `backend/tests/conftest.py` | In-memory SQLite engine, isolated `db_session`, `AsyncClient`, `create_test_movie()` helper |
| `backend/tests/test_movies.py` | list empty, list seeded, get by ID, 404, pagination, search by title |
| `backend/tests/test_entries.py` | create, 404, 409, list, get, update rating/favorite/notes, delete, filters, watch events (log/list/delete) |
| `backend/tests/test_lists.py` | create, list all, get by ID, 404, add item, delete, update |
| `backend/tests/test_tags.py` | create, list, 409 duplicate, delete, assign to entry |
| `backend/tests/test_stats.py` | empty stats, count, average rating, required keys |
| `backend/tests/test_sync.py` | pull empty, pull with entries, exclude future, push creates entry |
| `backend/pytest.ini` | `asyncio_mode = auto`, `testpaths = tests` |

**How to run:**
```bash
cd backend
venv\Scripts\activate        # Windows
pip install pytest pytest-asyncio httpx aiosqlite  # if not already installed
pytest -v
```

---

## Phase 6 — Local Windows Deployment ✅ DONE

| # | Task | Status |
|---|---|---|
| 6.1 | Build React frontend → copy output to `backend/static/` | ✅ via `npm run build` (vite.config.js outDir) |
| 6.2 | Configure FastAPI to serve static frontend at `/` | ✅ SPA catch-all in `main.py` |
| 6.3 | Test full single-server setup | ✅ FastAPI serves API + SPA from :8000 |
| 6.4 | `start.bat` one-click startup script | ✅ |
| 6.5 | `launcher.py` GUI | ✅ |
| 6.6 | Update launcher to build + serve production mode | ✅ **▶ Build & Serve** button added |
| 6.7 | Document full Windows setup in `README.md` | 🔲 |

---

## Phase 7 — Fujitsu Futro S740 / VPS Migration 🔲 PLANNED

| # | Task | Status |
|---|---|---|
| 7.1 | Install Ubuntu 22.04 on Futro S740 (or provision VPS) | 🔲 |
| 7.2 | Copy project + database to new machine | 🔲 |
| 7.3 | Set static local IP on Futro in router | 🔲 |
| 7.4 | Set up `gunicorn` + `nginx` reverse proxy | 🔲 |
| 7.5 | Add systemd service (auto-start on boot) | 🔲 |
| 7.6 | (Optional) Switch SQLite → PostgreSQL via `DATABASE_URL` | 🔲 |
| 7.7 | (Optional) Add HTTPS via Let's Encrypt / DuckDNS | 🔲 |
| 7.8 | Add JWT authentication (FastAPI-Users) for outside access | 🔲 |

---

## Phase 8 — Android Sync Support 🔲 PLANNED

| # | Task | Status |
|---|---|---|
| 8.1 | Sync endpoints skeleton already in `api/sync.py` | ✅ |
| 8.2 | Flesh out `GET /api/sync?since=` (delta pull) | 🔲 |
| 8.3 | Flesh out `POST /api/sync/push` (conflict resolution) | 🔲 |
| 8.4 | Set up React Native + Expo project | 🔲 |
| 8.5 | Implement local SQLite on Android (offline-first) | 🔲 |
| 8.6 | Implement background sync with conflict resolution | 🔲 |
| 8.7 | Add login screen + JWT token storage on Android | 🔲 |
| 8.8 | Port all MVP features to Android UI | 🔲 |
| 8.9 | Test sync between PC and Android | 🔲 |

---

## Phase 9 — German / Multilingual Support 🔶 IN PROGRESS

> Goal: German-first experience — UI in German by default, movie data (titles, overviews, genres) in German from TMDb, with a toggle to switch to English.

### Overview — What TMDb Supports

- TMDb fully supports `language=de-DE` on all API calls.
- German titles, overviews, and taglines are returned when available.
- TMDb automatically falls back to English when no German translation exists — no empty fields.
- Searching by German title (e.g. "Der Pate", "Das Schweigen der Lämmer") works correctly with `language=de-DE`.
- Genre names also come back localised ("Krimi", "Thriller", "Drama").

### Backend Tasks

| # | Task | Status | File |
|---|---|---|---|
| 9.1 | Add `language` param (default `de-DE`) to `search_movies()` | ✅ | `backend/app/services/tmdb.py` |
| 9.2 | Add `language` param (default `de-DE`) to `get_movie_details()` | ✅ | `backend/app/services/tmdb.py` |
| 9.3 | Add `language` param (default `de-DE`) to `import_movie()` | ✅ | `backend/app/services/tmdb.py` |
| 9.4 | Expose `lang` query param on `GET /api/search/tmdb` | ✅ | `backend/app/api/search.py` |
| 9.5 | Expose `lang` query param on `POST /api/search/tmdb/import/{id}` | ✅ | `backend/app/api/search.py` |
| 9.6 | Refactor `search.py` import endpoint to use service layer (removes duplicate code + auth inconsistency) | ✅ | `backend/app/api/search.py` |
| 9.7 | (Future) Add `overview_de` + `overview_en` columns to `movies` table | 🔲 | Alembic migration needed |
| 9.8 | (Future) Store both language overviews when importing | 🔲 | `tmdb.py` + `movie.py` |

### Frontend Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 9.9 | Install `react-i18next` + `i18next` | 🔲 | `npm install react-i18next i18next` |
| 9.10 | Create translation files `frontend/src/i18n/de.json` + `en.json` | 🔲 | All UI strings (nav, buttons, labels, empty states) |
| 9.11 | Init i18n in `main.jsx` — default locale `de`, fallback `en` | 🔲 | |
| 9.12 | Replace all hardcoded UI strings with `t('key')` calls | 🔲 | Across all pages |
| 9.13 | Add DE 🇩🇪 / EN 🇬🇧 language toggle in header/navbar | 🔲 | Persisted in `localStorage` |
| 9.14 | Wire language toggle → pass `lang=de-DE` or `lang=en-US` to all TMDb API calls | 🔲 | `AddMoviePage.jsx` search + import |
| 9.15 | (Future) UI toggle to re-fetch overview in alternate language | 🔲 | Requires 9.7/9.8 dual-overview storage |

### How the Cache Works With Languages

The `tmdb_cache` cache key includes all API params, including `language`. This means:
- A `de-DE` search for "Inception" and an `en-US` search for "Inception" are stored as **separate cache entries**.
- No cross-contamination between languages.
- Both are subject to the 7-day TTL independently.

---

## Extras / Nice-to-Have

| # | Task | Status |
|---|---|---|
| E.1 | CSV import/export of movie library | 🔲 |
| E.2 | Letterboxd CSV import | 🔲 |
| E.3 | Duplicate detection when adding movies | ✅ Done in F7 |
| E.4 | One-click SQLite database backup to `.zip` | 🔲 |
| E.5 | Rewatch reminders / rewatch list | 🔲 |
| E.6 | Franchise/collection grouping (TMDb collection data) | 🔲 |
| E.7 | Public profile page (shareable top-rated films) | 🔲 |
| E.8 | Multi-user support (separate accounts) | 🔲 |
| E.9 | `sync-server.js` (Node.js sync prototype) | 🔲 |

---

## Progress Overview

```
Phase 1  [██████████] 100% ✅  Planning & repo setup
Phase 2  [██████████] 100% ✅  Backend + DB
Phase 3  [██████████] 100% ✅  TMDb integration
Phase 4  [██████████] 100% ✅  React frontend — COMPLETE
Phase 5  [█         ]  10% 🔶  Testing + AI (5.1 done, 5.4 next)
Phase 6  [█████████ ]  90% ✅  Local deployment (README remaining)
Phase 7  [          ]   0% 🔲  Server/VPS
Phase 8  [█         ]  10% 🔲  (sync.py skeleton done)
Phase 9  [████      ]  40% 🔶  German i18n (backend done, frontend pending)
```

---

## ⏳ Immediate Next Steps

1. **Run the test suite locally:** `cd backend && venv\Scripts\activate && pytest -v`
2. **Phase 9.9–9.14** — Add `react-i18next` to frontend + DE/EN language toggle in header.
3. **Phase 5.4** — Build `backend/app/services/llm.py` (LLM proxy: OpenAI / Gemini / Ollama).
4. **Phase 5.5–5.8** — Build `/api/ai/` endpoints (recommendations, stats report, tag suggestions, NL search).
5. **Phase 6.7** — Update `README.md` with full Windows setup instructions.

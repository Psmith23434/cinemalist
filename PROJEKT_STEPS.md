# CinemaList — Project Steps

> Last updated: 2026-04-06 10:31 CEST
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
| 2.2 | Create FastAPI app entry point (`app/main.py`) | ✅ | `backend/app/main.py` (2.1 KB) |
| 2.3 | Configure SQLAlchemy + Alembic (`database.py`, `alembic.ini`) | ✅ | `backend/alembic.ini`, `backend/app/core/` |
| 2.4 | Write all SQLAlchemy ORM models | ✅ | `backend/app/models/` |
| | → `movies`, `genres`, `movie_genres` | ✅ | |
| | → `entries`, `watch_events` | ✅ | |
| | → `tags`, `entry_tags` | ✅ | |
| | → `lists`, `list_items` | ✅ | |
| | → `tmdb_cache`, `sync_log` | ✅ | |
| 2.5 | Write Alembic migration (`0001_initial_tables.py`) | ✅ | `backend/alembic/versions/0001_initial_tables.py` |
| 2.6 | Apply migration → `cinemalist.db` created locally | ✅ | Applied via `launcher.py` → Start Server (runs `alembic upgrade head` automatically). `cinemalist.db` exists at `backend/cinemalist.db`. Not in repo (`.gitignore`d). |
| 2.7 | Build `run.py` helper script | ✅ | `backend/run.py` |
| 2.8 | Build GUI launcher (`launcher.py`) with Start/Stop/Open Docs | ✅ | `/launcher.py` (17.9 KB) — runs `alembic upgrade head` then starts uvicorn on port 8000 |
| 2.9 | Add `start.bat` one-click startup script | ✅ | `/start.bat` |

> **How to start the backend:** Run `python launcher.py` from `E:\Projects\Cine`, then click **▶ Start Server**. The launcher automatically runs `alembic upgrade head` first (safe to re-run — skips already-applied migrations), then starts uvicorn on `http://localhost:8000`. Swagger UI is available at `http://localhost:8000/docs`.

> **Note (Alembic safe to re-run):** Running `alembic upgrade head` again after a `git pull` is always safe — Alembic tracks applied migrations in the `alembic_version` table inside `cinemalist.db`. It skips already-applied migrations and only runs new ones. Your existing data is never overwritten.

> **⚠️ Important — cinemalist.db:** The local `cinemalist.db` was wiped on 2026-04-06 during smoke-testing because the `watch_events` table was missing the `uuid` column (created before the column was added to the model). This is expected at this stage. Once Alembic is used for all schema changes, the DB will never need to be wiped again. The fix: always run `alembic upgrade head` after a `git pull` — never manually delete the DB once real data exists.

---

## Phase 3 — TMDb API Integration ✅ DONE

| # | Task | Status | Evidence |
|---|---|---|---|
| 3.1 | Create `app/services/tmdb.py` — search, detail, import | ✅ | `backend/app/services/tmdb.py` (7.6 KB) |
| 3.2 | Implement cache-first logic (7-day TTL in `tmdb_cache`) | ✅ | Inside `tmdb.py` |
| 3.3 | ~~Download + store poster images to `media/posters/`~~ | 🚫 | **Permanently won't do.** Posters served via TMDb CDN: `https://image.tmdb.org/t/p/w500/{poster_path}`. Stored as path in `movies.poster_path`. |
| 3.4 | Write Pydantic schemas | ✅ | `schemas/movie.py`, `schemas/entry.py`, `schemas/stats.py`, `schemas/list.py` |
| 3.5 | Build API router: `GET /api/search/tmdb?q=` | ✅ | `backend/app/api/search.py` |
| 3.6 | Build API router: `POST /api/search/tmdb/import/{tmdb_id}` | ✅ | `backend/app/api/search.py` |
| 3.7 | Build API router: `GET /api/movies/` with genre/sort/direction filters | ✅ | `backend/app/api/movies.py` (5.9 KB) |
| 3.8 | Build CRUD for entries: `POST/GET/PUT/DELETE /api/entries/` | ✅ | `backend/app/api/entries.py` (5.0 KB) |
| 3.9 | Build API routers: genres, tags, lists, stats, sync | ✅ | `genres.py`, `tags.py`, `lists.py`, `stats.py`, `sync.py` |
| 3.10 | Smoke-test all endpoints in Swagger UI (`/docs`) | ✅ | All 6 steps passed — see details below |

### 3.10 Smoke-Test Results (2026-04-06) ✅ ALL PASSED

| Step | Endpoint | Status | Notes |
|---|---|---|---|
| S1 | `GET /` health check | ✅ | Returns `{"status": "ok"}` |
| S2 | `GET /api/search/tmdb?q=inception` | ✅ | Returns TMDb results. **Note:** use "API-Token für Lesezugriff" (long Bearer token) in `.env` as `TMDB_API_KEY`, NOT the short "API-Schlüssel". |
| S3 | `POST /api/search/tmdb/import/27205` (Inception) | ✅ | 201 Created. Bug fixed: `MovieRead` schema was receiving `MovieGenre` join objects instead of `Genre` objects — fixed in `schemas/movie.py` with `@field_validator("genres", mode="before")` that unwraps `.genre` attribute. |
| S3b | `POST /api/search/tmdb/import/157336` (Interstellar) | ✅ | 201 Created. Clean import with genres Adventure, Drama, Science Fiction. |
| S4 | `GET /api/movies/` | ✅ | Returns both movies with all metadata. |
| S5 | `POST /api/entries/` | ✅ | 201 Created. Entry + watch_event inserted and committed. Bug fixed: `watch_events` table was missing `uuid` column — fixed in Alembic migration `0001_initial_tables.py`. |
| S6 | `GET /api/stats/` | ✅ | Returns `total_watched: 1`, `average_rating: 4`, `total_runtime_minutes: 148`, correct genre breakdown and rating distribution. |

---

## Phase 4 — React Frontend / UI 🔶 IN PROGRESS

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
| 4.10 | Wire frontend to live backend (replace mock data with API calls) | ⏳ **UP NEXT** |
| 4.11 | Build React frontend as production bundle into `backend/static/` | 🔲 |

> **Current status:** Frontend running at `http://localhost:5173`. All pages render. Frontend is **not yet wired to the backend** — empty states everywhere. This is the next major task now that Phase 3 smoke-test is fully complete.

> **Mantine version note:** Project uses **Mantine v7**. A future upgrade to v9 is documented in `PROJECT_PLAN.md` Section 11, to be done after Phase 5 (testing) when the app is fully working end-to-end.

### 4.10 — Frontend Wiring Plan (Up Next)

| Sub-task | Page | API endpoint |
|---|---|---|
| 4.10.1 | Library page | `GET /api/movies/` → render real poster cards |
| 4.10.2 | Search page | `GET /api/search/tmdb?q=` → live search-as-you-type |
| 4.10.3 | Import button | `POST /api/search/tmdb/import/{tmdb_id}` |
| 4.10.4 | Movie Detail / Add Entry modal | `POST /api/entries/` → save rating, notes, watch date |
| 4.10.5 | Entry Edit / Delete | `PUT /api/entries/{id}`, `DELETE /api/entries/{id}` |
| 4.10.6 | Statistics page | `GET /api/stats/` → real totals, genres, rating chart |
| 4.10.7 | Lists page | `GET/POST /api/lists/`, `POST /api/lists/{id}/items` |
| 4.10.8 | Tags | `GET/POST /api/tags/` + wire to entry form |

---

## Phase 5 — Testing, Polish & AI Integration 🔲 PLANNED

| # | Task | Status |
|---|---|---|
| 5.1 | Write `pytest` test suite for backend (`backend/tests/`) | 🔲 |
| 5.2 | Add database indexes on frequently queried columns | 🔲 |
| 5.3 | Add error handling: missing posters, API failures, duplicates | 🔲 |
| 5.4 | Implement `app/services/llm.py` — LLM proxy connection | 🔲 |
| 5.5 | Build `GET /api/ai/recommend` — personalised recommendations | 🔲 |
| 5.6 | Build `GET /api/ai/stats-report` — narrative stats summary | 🔲 |
| 5.7 | Build `POST /api/ai/suggest-tags` — auto-tag suggestions | 🔲 |
| 5.8 | Build `GET /api/ai/search` — natural language library search | 🔲 |
| 5.9 | Add LLM response caching (`llm_cache` table) | 🔲 |
| 5.10 | Add "For You ✨" tab in React Statistics page | 🔲 |

---

## Phase 6 — Local Windows Deployment 🔲 PLANNED

| # | Task | Status |
|---|---|---|
| 6.1 | Build React frontend → copy output to `backend/static/` | 🔲 |
| 6.2 | Configure FastAPI to serve static frontend at `/` | 🔲 |
| 6.3 | Test full single-server setup (FastAPI serves both API + UI) | 🔲 |
| 6.4 | `start.bat` one-click startup script | ✅ |
| 6.5 | `launcher.py` GUI (Start / Stop / Open Docs / Open Folder) | ✅ |
| 6.6 | Update launcher to build + serve production mode | 🔲 |
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

## Extras / Nice-to-Have 🔲 PLANNED

| # | Task | Status |
|---|---|---|
| E.1 | CSV import/export of movie library | 🔲 |
| E.2 | Letterboxd CSV import | 🔲 |
| E.3 | Duplicate detection when adding movies | 🔲 |
| E.4 | One-click SQLite database backup to `.zip` | 🔲 |
| E.5 | Rewatch reminders / rewatch list | 🔲 |
| E.6 | Franchise/collection grouping (TMDb collection data) | 🔲 |
| E.7 | Public profile page (shareable top-rated films) | 🔲 |
| E.8 | Multi-user support (separate accounts) | 🔲 |
| E.9 | `sync-server.js` (Node.js sync prototype, present in repo root) | 🔲 |

---

## Current Repo File Inventory

```
/
├── PROJECT_PLAN.md          ✅ full project spec
├── PROJEKT_STEPS.md         ✅ this file
├── README.md                ✅
├── launcher.py              ✅ GUI launcher (tkinter, dark cinema theme)
│                               Starts backend: alembic upgrade head → uvicorn :8000
├── start.bat                ✅ one-click CMD startup
├── cinemalist.html          ✅ placeholder / future static entry
├── sync-server.js           ✅ Node.js sync prototype (future)
└── backend/
    ├── .env                 ✅ local only — contains TMDB_API_KEY (not in repo)
    │                           ⚠️  Use "API-Token für Lesezugriff" (long Bearer token)
    │                               NOT the short "API-Schlüssel"
    ├── .env.example         ✅
    ├── cinemalist.db        ⚠️  local only — SQLite DB (.gitignored)
    │                           Safe to delete during dev. Once Alembic is used for
    │                           all changes, never delete manually again.
    ├── README.md            ✅
    ├── alembic.ini          ✅
    ├── requirements.txt     ✅
    ├── run.py               ✅
    ├── alembic/
    │   └── versions/
    │       └── 0001_initial_tables.py  ✅ applied — all 11 tables created
    └── app/
        ├── main.py          ✅
        ├── models/          ✅ (all 11 ORM models)
        ├── schemas/
        │   ├── common.py    ✅
        │   ├── movie.py     ✅ fixed 2026-04-06: genres field now unwraps MovieGenre
        │   │                   join objects via @field_validator
        │   ├── entry.py     ✅
        │   ├── watch_event.py ✅
        │   ├── list.py      ✅
        │   ├── tag.py       ✅
        │   ├── genre.py     ✅
        │   └── stats.py     ✅
        ├── services/
        │   └── tmdb.py      ✅ (search, detail, cache, import)
        ├── api/
        │   ├── search.py    ✅ (TMDb search + import)
        │   ├── movies.py    ✅ (CRUD + filters)
        │   ├── entries.py   ✅ (CRUD + watch events)
        │   ├── genres.py    ✅
        │   ├── tags.py      ✅
        │   ├── lists.py     ✅
        │   ├── stats.py     ✅
        │   └── sync.py      ✅ (skeleton)
        └── core/            ✅ (config, database session)
```

> **Local-only files (not in repo, .gitignored):**
> - `backend/cinemalist.db` — SQLite database, created by `alembic upgrade head` on first launcher start
> - `backend/.env` — contains `TMDB_API_KEY` (use long Bearer token!) and other secrets

---

## ⏳ Immediate Next Steps

1. **Wire frontend to backend (Phase 4.10)** — replace mock/empty states in React with real API calls to `http://localhost:8000/api/`. Work through sub-tasks 4.10.1 → 4.10.8 in order.

2. **Set up Alembic going forward** — any future model change must go through an Alembic migration (`alembic revision --autogenerate -m "description"`) instead of dropping the DB.

---

## Progress Overview

```
Phase 1  [██████████] 100% ✅  Planning & repo setup
Phase 2  [██████████] 100% ✅  Backend + DB (migration applied)
Phase 3  [██████████] 100% ✅  TMDb integration (all 6 smoke-test steps passed)
Phase 4  [████████░░]  80% 🔶  React frontend (all pages built, wiring to backend up next)
Phase 5  [          ]   0% 🔲  Testing + AI
Phase 6  [██        ]  20% 🔲  (start.bat + launcher.py done, rest needs frontend build)
Phase 7  [          ]   0% 🔲  Server/VPS
Phase 8  [█         ]  10% 🔲  (sync.py skeleton done)
```

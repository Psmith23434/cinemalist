# CinemaList — Project Steps

> Last updated: 2026-04-05
> **Legend:** ✅ Done · 🔶 In Progress · ⏳ Up Next · 🔲 Planned

---

## Phase 1 — Planning & Repository Setup ✅ DONE

| # | Task | Status |
|---|---|---|
| 1.1 | Create GitHub repository | ✅ |
| 1.2 | Define full project plan (`PROJECT_PLAN.md`) | ✅ |
| 1.3 | Set up folder structure (`backend/`, `frontend/`, etc.) | ✅ |
| 1.4 | Add `.gitignore`, `.env.example`, `README.md` | ✅ |
| 1.5 | Choose tech stack (FastAPI + SQLite + React + TMDb) | ✅ |
| 1.6 | Define database schema (all 11 tables) | ✅ |
| 1.7 | Define API design & sync strategy | ✅ |

---

## Phase 2 — Backend & Database ✅ DONE

| # | Task | Status |
|---|---|---|
| 2.1 | Set up Python virtual environment + `requirements.txt` | ✅ |
| 2.2 | Create FastAPI app entry point (`app/main.py`) | ✅ |
| 2.3 | Configure SQLAlchemy + Alembic (`database.py`, `alembic.ini`) | ✅ |
| 2.4 | Write all SQLAlchemy ORM models | ✅ |
| | → `movies`, `genres`, `movie_genres` | ✅ |
| | → `entries`, `watch_events` | ✅ |
| | → `tags`, `entry_tags` | ✅ |
| | → `lists`, `list_items` | ✅ |
| | → `tmdb_cache`, `sync_log` | ✅ |
| 2.5 | Write Alembic migration (`0001_initial_tables.py`) | ✅ |
| 2.6 | Apply migration → `cinemalist.db` created | ✅ |
| 2.7 | Build GUI launcher (`launcher.py`) with Start/Stop/Open Docs | ✅ |

---

## Phase 3 — TMDb API Integration ✅ DONE

> Merged via PR #3 on 2026-04-05

| # | Task | Status |
|---|---|---|
| 3.1 | Create `app/services/tmdb.py` — search, detail, import | ✅ |
| 3.2 | Implement cache-first logic (7-day TTL in `tmdb_cache`) | ✅ |
| 3.3 | Download + store poster images to `media/posters/` | 🔲 |
| 3.4 | Write Pydantic schemas (`schemas/movie.py`, `schemas/entry.py`, `schemas/stats.py`) | ✅ |
| 3.5 | Build API router: `GET /api/search/tmdb?q=` | ✅ |
| 3.6 | Build API router: `POST /api/search/tmdb/import` | ✅ |
| 3.7 | Build API router: `GET /api/movies/` with genre/sort/direction filters | ✅ |
| 3.8 | Build CRUD for entries: `POST/GET/PUT/DELETE /api/entries/` | ✅ |
| 3.9 | Build API routers: genres, tags, lists, stats, sync | ✅ |
| 3.10 | Test all endpoints in Swagger UI (`/docs`) | ⏳ |

> **Note (3.3):** Poster images are currently served via TMDb CDN URLs (`poster_url` computed field).
> Local caching to `media/posters/` is a nice-to-have for offline use — deferred to Phase 5/6.

---

## Phase 4 — React Frontend / UI ⏳ UP NEXT

| # | Task | Status |
|---|---|---|
| 4.1 | Set up React + Vite project in `frontend/` | 🔲 |
| 4.2 | Install Mantine UI component library | 🔲 |
| 4.3 | Build Movie Grid / Library page (poster cards) | 🔲 |
| 4.4 | Build Movie Search page (live TMDb search-as-you-type) | 🔲 |
| 4.5 | Build Movie Detail page (rating, notes, watch date) | 🔲 |
| 4.6 | Build Statistics page (totals, avg rating, genre breakdown) | 🔲 |
| 4.7 | Build Lists & Tags management | 🔲 |
| 4.8 | Add dark mode toggle | 🔲 |
| 4.9 | Configure CORS between Vite (5173) and FastAPI (8000) | 🔲 |
| 4.10 | Build React frontend as production bundle into `backend/static/` | 🔲 |

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
| 6.4 | Write `start.bat` one-click startup script | ✅ |
| 6.5 | Update `launcher.py` GUI to use production mode | 🔲 |
| 6.6 | Document full Windows setup in `README.md` | 🔲 |

---

## Phase 7 — Fujitsu Futro S740 / VPS Migration 🔲 PLANNED

| # | Task | Status |
|---|---|---|
| 7.1 | Install Ubuntu 22.04 on Futro S740 (or provision VPS) | 🔲 |
| 7.2 | Copy project + database + media folder to new machine | 🔲 |
| 7.3 | Set static local IP on Futro in router | 🔲 |
| 7.4 | Set up `gunicorn` + `nginx` reverse proxy | 🔲 |
| 7.5 | Add systemd service (auto-start on boot) | 🔲 |
| 7.6 | (Optional) Switch SQLite → PostgreSQL via SQLAlchemy `DATABASE_URL` | 🔲 |
| 7.7 | (Optional) Add HTTPS via Let's Encrypt / DuckDNS | 🔲 |
| 7.8 | Add JWT authentication (FastAPI-Users) for outside access | 🔲 |

---

## Phase 8 — Android Sync Support 🔲 PLANNED

| # | Task | Status |
|---|---|---|
| 8.1 | Build sync endpoints: `GET /api/sync?since=` | 🔲 |
| 8.2 | Build sync push: `POST /api/sync/push` | 🔲 |
| 8.3 | Set up React Native + Expo project | 🔲 |
| 8.4 | Implement local SQLite on Android (offline-first) | 🔲 |
| 8.5 | Implement background sync with conflict resolution | 🔲 |
| 8.6 | Add login screen + JWT token storage on Android | 🔲 |
| 8.7 | Port all MVP features to Android UI | 🔲 |
| 8.8 | Test sync between PC and Android | 🔲 |

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

---

## Progress Overview

```
Phase 1  [██████████] 100% ✅
Phase 2  [██████████] 100% ✅
Phase 3  [█████████░]  90% ✅ (3.3 poster local cache deferred; 3.10 manual test pending)
Phase 4  [          ]   0% ⏳ ← YOU ARE HERE
Phase 5  [          ]   0% 🔲
Phase 6  [░         ]   5% 🔲 (start.bat exists)
Phase 7  [          ]   0% 🔲
Phase 8  [          ]   0% 🔲
```

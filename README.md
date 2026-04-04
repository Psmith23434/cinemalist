# 🎬 CinemaList

A beautiful, feature-rich personal movie tracking app — built with a Python/FastAPI backend and React frontend, designed for local PC use first with a clear path to VPS deployment and Android sync.

> 📄 **Full project plan, architecture decisions, database schema, and development roadmap:** see [`PROJECT_PLAN.md`](./PROJECT_PLAN.md)

---

## Features

- 🔍 **Movie Search** — Live search via TMDb API with posters, genres, runtime, and full metadata
- 📋 **Movie Library** — Track watched movies, a watchlist, and dropped films
- ⭐ **Ratings & Notes** — Personal ratings (0–10) + notes/reviews per movie
- ❤️ **Favourites** — Mark your all-time favourites
- 📅 **Watch History** — Log every viewing with date and platform (Netflix, Cinema, etc.)
- 🗂️ **Lists & Tags** — Custom collections and tags (e.g. "Nolan Films", `#rewatched`)
- 📊 **Stats Dashboard** — Total watched, average rating, top genres, yearly breakdown
- 🌙 **Dark / Light Mode** — Auto-detects system preference, manually toggleable
- 🔃 **Sort & Filter** — By rating, genre, year, watch date, and more
- 💾 **Local Storage** — All data stored in a local SQLite database (no cloud required)
- 🔄 **Sync-Ready Architecture** — Designed from day one for future Android app sync

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11 + FastAPI + SQLAlchemy + Alembic |
| **Database** | SQLite (local) → PostgreSQL (VPS later) |
| **Frontend** | React + Vite + Mantine UI |
| **Movie API** | [TMDb](https://www.themoviedb.org/) (free API key required) |
| **Local Server** | Uvicorn (ASGI) |

---

## Quick Start (Windows PC)

### 1. Prerequisites

Install the following (one-time setup):

- [Python 3.11+](https://python.org/downloads) — check **"Add Python to PATH"** during install
- [Git](https://git-scm.com/download/win)
- [Node.js 20 LTS](https://nodejs.org)
- [VS Code](https://code.visualstudio.com) (recommended editor)

### 2. Clone the Repo

```bash
git clone https://github.com/Psmith23434/cinemalist.git
cd cinemalist
```

### 3. Set Up the Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
copy .env.example .env
```

```ini
TMDB_API_KEY=your_tmdb_api_key_here
DATABASE_URL=sqlite:///./cinemalist.db
MEDIA_DIR=./media
SECRET_KEY=change_this_to_a_random_string
DEBUG=True
```

> Get a free TMDb API key at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Start the Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs available at: **http://localhost:8000/docs**

### 7. Start the Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

App available at: **http://localhost:5173**

---

## Project Structure

```
cinemalist/
├── backend/
│   ├── app/
│   │   ├── main.py          ← FastAPI entry point
│   │   ├── models/          ← SQLAlchemy database models
│   │   ├── schemas/         ← Pydantic request/response schemas
│   │   ├── routers/         ← API route handlers
│   │   └── services/        ← Business logic (TMDb, sync)
│   ├── migrations/          ← Alembic migration files
│   ├── media/posters/       ← Downloaded poster images
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/             ← API client (fetch wrappers)
│   └── vite.config.js
├── PROJECT_PLAN.md          ← Full architecture & roadmap
└── README.md
```

---

## Android Sync (Future — Phase 8)

The app is architected from day one to support Android sync. The FastAPI backend exposes sync endpoints that an Android app (React Native / Expo) will use:

```
[Android App]  ←→  HTTPS  ←→  [FastAPI Backend]  ←→  [PostgreSQL]
                                      ↕
                              [React Browser UI]
```

- All user records have UUIDs and `updated_at` timestamps for conflict-free sync
- Soft deletes (`deleted_at`) ensure Android always knows what was removed
- Sync endpoints: `GET /api/v1/sync?since=...` and `POST /api/v1/sync/push`

See [`PROJECT_PLAN.md → Section 6`](./PROJECT_PLAN.md#6-sync--future-android-app) for the full sync design.

---

## VPS Deployment (Future — Phase 7)

When ready to move from local PC to a server:

1. Switch `DATABASE_URL` to PostgreSQL — SQLAlchemy handles the rest automatically
2. Set up Nginx as a reverse proxy
3. Add HTTPS via Let's Encrypt (free)
4. Use `gunicorn` + `uvicorn` workers for production

Recommended VPS: **Hetzner CX22** (~€5/month, Germany-based).

See [`PROJECT_PLAN.md → Phase 7`](./PROJECT_PLAN.md#phase-7--vps-migration) for the full migration guide.

---

## Development Roadmap

| Phase | Description | Status |
|---|---|---|
| 1 | Planning & repo setup | ✅ Done |
| 2 | Backend & database (FastAPI + SQLAlchemy) | 🔧 In progress |
| 3 | TMDb API integration | ⏳ Upcoming |
| 4 | React frontend / UI | ⏳ Upcoming |
| 5 | Testing & polish | ⏳ Upcoming |
| 6 | Local PC deployment (start.bat) | ⏳ Upcoming |
| 7 | VPS migration (PostgreSQL + Nginx) | ⏳ Future |
| 8 | Android app + sync | ⏳ Future |

Full details for each phase in [`PROJECT_PLAN.md`](./PROJECT_PLAN.md).

---

## Contributing / AI Workflow

This project uses a branch-based review workflow:

1. Changes are proposed on a feature branch
2. A Pull Request is opened for review
3. Code is reviewed in the **Files Changed** tab before merging
4. `git pull` on your PC to get the latest after merging

---

*Built with ❤️ using Python, FastAPI, React, and TMDb.*

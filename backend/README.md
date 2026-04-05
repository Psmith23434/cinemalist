# CinemaList — Backend

FastAPI + SQLAlchemy async backend for the CinemaList movie tracking app.

## Quick Start (Windows)

```bash
# 1. Clone and enter the backend folder
git clone https://github.com/Psmith23434/cinemalist.git
cd cinemalist/backend

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the example env file and fill in your TMDb API key
copy .env.example .env
# Edit .env and set TMDB_API_KEY=your_key_here

# 5. Run the dev server
python run.py
```

The API will be live at **http://localhost:8000**

Interactive API docs: **http://localhost:8000/docs**

## Project Structure

```
backend/
├── app/
│   ├── main.py            # FastAPI app + router registration
│   ├── core/
│   │   ├── config.py      # Settings loaded from .env
│   │   └── database.py    # Async SQLAlchemy engine + session
│   ├── models/            # SQLAlchemy ORM models (one file per table)
│   ├── schemas/           # Pydantic request/response schemas
│   └── api/               # Route handlers (one file per resource)
│       ├── movies.py      # GET/POST/DELETE /api/movies
│       ├── entries.py     # Full CRUD /api/entries  
│       ├── lists.py       # Lists + list items
│       ├── tags.py        # Tag listing
│       ├── genres.py      # Genre listing
│       ├── stats.py       # Statistics dashboard data
│       ├── search.py      # TMDb search + detail (with caching)
│       └── sync.py        # Delta sync endpoint for future Android app
├── alembic/               # Database migrations
├── alembic.ini
├── requirements.txt
├── run.py                 # Dev server entry point
└── .env.example
```

## Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/movies` | List/search local movies |
| POST | `/api/movies` | Add a movie manually |
| GET | `/api/entries` | List all user entries (watched, ratings, notes) |
| POST | `/api/entries` | Add a new entry |
| PATCH | `/api/entries/{id}` | Update rating, notes, tags, etc. |
| DELETE | `/api/entries/{id}` | Soft-delete an entry |
| GET | `/api/search/tmdb?q=inception` | Search TMDb (cached) |
| GET | `/api/search/tmdb/{tmdb_id}` | Get full TMDb movie details |
| GET | `/api/stats` | Statistics for the dashboard |
| GET | `/api/lists` | All user lists |
| GET | `/api/sync/delta?device_id=x&since=...` | Delta sync for Android |

Full interactive docs at `/docs` when the server is running.

## Environment Variables

See `.env.example` for all available settings. Required:
- `TMDB_API_KEY` — get yours free at https://www.themoviedb.org/settings/api

## Getting a TMDb API Key

1. Create a free account at https://www.themoviedb.org/
2. Go to Settings → API
3. Request an API key (type: Developer, personal use)
4. Copy the **API Key (v3 auth)** into your `.env` file

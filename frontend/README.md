# CinemaList — Frontend

React + Vite frontend for CinemaList.

## Setup

```bash
cd frontend
npm install
npm run dev
```

Requires the FastAPI backend running at `http://localhost:8000`.

Open `http://localhost:5173` in your browser.

## Build for production

```bash
npm run build
```

Builds to `../backend/static/` so FastAPI can serve the built frontend directly.

## Pages

| Route | Page |
|---|---|
| `/` | Library — all watched films |
| `/watchlist` | Films to watch |
| `/favourites` | Hearted films |
| `/lists` | Custom collections |
| `/tags` | Tag management |
| `/stats` | Statistics dashboard |
| `/add` | Search TMDb + add film |
| `/movie/:id` | Film detail, rating, notes, watch history |

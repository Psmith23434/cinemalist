# 🎬 CinemaList

A beautiful, feature-rich movie tracking app — PC web app with planned Android sync.

---

## Features

- **Movie Library** — Track watched movies, a watchlist, and dropped films
- **TMDB Integration** — Live movie search with posters, overviews, genres, runtime, director
- **Ratings & Notes** — 5-star ratings + personal notes per movie
- **Favorites** — Mark your all-time favorites
- **Stats Dashboard** — Rating distribution, top genres, top-rated list, total hours watched
- **Dark / Light Mode** — Auto-detects system preference, manually toggleable
- **Sort & Filter** — Sort by date, rating, title, year; filter by genre
- **Grid / List View** — Toggle between card grid and compact list
- **Export / Import** — JSON backup and restore
- **Keyboard Shortcuts** — `Ctrl+K` to add a movie, `Esc` to close modals

---

## Quick Start (No Installation)

Just open `cinemalist.html` in any modern browser (Chrome, Firefox, Edge).

> **Note:** Data is stored in-memory while the tab is open. For persistent storage on your PC, see the section below.

---

## Enabling Persistent Storage (PC)

The app uses in-memory state by default. To persist data on your local PC, open `cinemalist.html` in a text editor and replace the two stub functions:

```js
function loadState() {
  const saved = localStorage.getItem('cinemalist');
  if (saved) { try { const d = JSON.parse(saved); state.movies = d.movies || []; state.settings = {...state.settings, ...d.settings}; } catch{} }
}

function saveState() {
  localStorage.setItem('cinemalist', JSON.stringify({ movies: state.movies, settings: state.settings }));
}
```

---

## TMDB API Key (Live Movie Search)

1. Go to https://www.themoviedb.org/settings/api and create a free account
2. Copy your **API Key (v3 auth)**
3. In CinemaList → **Settings → TMDB API Key → Configure** — paste your key
4. Live search will now show real posters and full metadata

---

## Android Sync (Future)

```
[CinemaList PC App]  ←→  [sync-server.js (Node.js)]  ←→  [CinemaList Android App]
      localhost                  localhost:3000                  local network
```

### Local Sync Server

```bash
npm install express cors
node sync-server.js
```

The Android app connects to `http://<your-PC-IP>:3000` on the same Wi-Fi.

### VPS Deployment

When ready to move to a VPS:
1. Copy `cinemalist.html` and `sync-server.js` to your server
2. Run behind nginx or caddy with HTTPS
3. Update the Android app's server URL

---

## Tech Stack

- Vanilla HTML/CSS/JS — no framework, no build step
- [TMDB API](https://www.themoviedb.org/) — movie database
- [Lucide Icons](https://lucide.dev/) — icon library
- Google Fonts — Instrument Serif + DM Sans

---

## Roadmap

- [ ] localStorage persistence (see above)
- [ ] Android companion app (Kotlin / React Native)
- [ ] Real-time sync via WebSocket
- [ ] VPS deployment guide
- [ ] Custom lists / collections
- [ ] Watch party mode
- [ ] Letterboxd import

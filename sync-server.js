/**
 * CinemaList Sync Server
 * Run: node sync-server.js
 * Exposes a simple REST API for Android app sync.
 *
 * Install dependencies: npm install express cors
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'cinemalist-data.json');

app.use(cors());
app.use(express.json({ limit: '10mb' }));

function loadData() {
  try {
    if (fs.existsSync(DATA_FILE)) return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
  } catch {}
  return { movies: [], lastSync: null };
}

function saveData(data) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

// GET /api/movies
app.get('/api/movies', (req, res) => {
  const data = loadData();
  res.json({ movies: data.movies, lastSync: data.lastSync });
});

// POST /api/sync — full sync
app.post('/api/sync', (req, res) => {
  const { movies } = req.body;
  if (!Array.isArray(movies)) return res.status(400).json({ error: 'Invalid data' });
  const data = { movies, lastSync: new Date().toISOString() };
  saveData(data);
  res.json({ ok: true, count: movies.length, lastSync: data.lastSync });
});

// POST /api/movie — add or update single movie
app.post('/api/movie', (req, res) => {
  const movie = req.body;
  if (!movie || !movie.id) return res.status(400).json({ error: 'Invalid movie' });
  const data = loadData();
  const idx = data.movies.findIndex(m => m.id === movie.id);
  if (idx >= 0) data.movies[idx] = movie;
  else data.movies.push(movie);
  data.lastSync = new Date().toISOString();
  saveData(data);
  res.json({ ok: true });
});

// DELETE /api/movie/:id
app.delete('/api/movie/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const data = loadData();
  data.movies = data.movies.filter(m => m.id !== id);
  data.lastSync = new Date().toISOString();
  saveData(data);
  res.json({ ok: true });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`CinemaList Sync Server running on http://localhost:${PORT}`);
  console.log(`For Android on same Wi-Fi, use http://<your-pc-ip>:${PORT}`);
});

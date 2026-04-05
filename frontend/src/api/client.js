const BASE = 'http://localhost:8000/api';

async function req(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(BASE + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // Movies
  getMovies:      (params = {}) => req('GET', '/movies/?' + new URLSearchParams(params)),
  getMovie:       (id)          => req('GET', `/movies/${id}`),
  deleteMovie:    (id)          => req('DELETE', `/movies/${id}`),

  // Entries
  getEntries:     (params = {}) => req('GET', '/entries/?' + new URLSearchParams(params)),
  getEntry:       (id)          => req('GET', `/entries/${id}`),
  createEntry:    (data)        => req('POST', '/entries/', data),
  updateEntry:    (id, data)    => req('PATCH', `/entries/${id}`, data),
  deleteEntry:    (id)          => req('DELETE', `/entries/${id}`),

  // Watch events
  addWatch:       (entryId, data) => req('POST', `/entries/${entryId}/watches`, data),
  getWatches:     (entryId)       => req('GET', `/entries/${entryId}/watches`),
  deleteWatch:    (entryId, wid)  => req('DELETE', `/entries/${entryId}/watches/${wid}`),

  // Search
  searchTmdb:     (q, page = 1)  => req('GET', `/search/tmdb?q=${encodeURIComponent(q)}&page=${page}`),
  importTmdb:     (tmdbId)       => req('POST', `/search/tmdb/import/${tmdbId}`),

  // Genres
  getGenres:      ()             => req('GET', '/genres/'),

  // Tags
  getTags:        ()             => req('GET', '/tags/'),
  createTag:      (data)         => req('POST', '/tags/', data),
  deleteTag:      (id)           => req('DELETE', `/tags/${id}`),
  attachTag:      (entryId, tagId) => req('POST', `/tags/entry/${entryId}/${tagId}`),
  detachTag:      (entryId, tagId) => req('DELETE', `/tags/entry/${entryId}/${tagId}`),

  // Lists
  getLists:       ()             => req('GET', '/lists/'),
  getList:        (id)           => req('GET', `/lists/${id}`),
  createList:     (data)         => req('POST', '/lists/', data),
  updateList:     (id, data)     => req('PATCH', `/lists/${id}`, data),
  deleteList:     (id)           => req('DELETE', `/lists/${id}`),
  addToList:      (listId, entryId) => req('POST', `/lists/${listId}/entries/${entryId}`),
  removeFromList: (listId, entryId) => req('DELETE', `/lists/${listId}/entries/${entryId}`),

  // Stats
  getStats:       ()             => req('GET', '/stats/overview'),
};

export const posterUrl = (path, size = 'w342') =>
  path ? `https://image.tmdb.org/t/p/${size}${path}` : null;

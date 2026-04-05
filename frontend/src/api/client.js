/**
 * Thin API client — all requests go to /api/v1 (proxied by Vite to FastAPI).
 */

const BASE = '/api/v1';

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get:    (path)        => request('GET',    path),
  post:   (path, body)  => request('POST',   path, body),
  patch:  (path, body)  => request('PATCH',  path, body),
  put:    (path, body)  => request('PUT',    path, body),
  delete: (path)        => request('DELETE', path),
};

// ── Movies ──────────────────────────────────────────────────────────────────
export const moviesApi = {
  search:  (q) => api.get(`/search?q=${encodeURIComponent(q)}`),
  import:  (tmdb_id) => api.post(`/movies/import/${tmdb_id}`),
  detail:  (tmdb_id) => api.get(`/movies/${tmdb_id}`),
};

// ── Entries ──────────────────────────────────────────────────────────────────
export const entriesApi = {
  list:    (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== '' && v != null)
    ).toString();
    return api.get(`/entries${qs ? '?' + qs : ''}`);
  },
  get:     (id)    => api.get(`/entries/${id}`),
  create:  (body)  => api.post('/entries', body),
  update:  (id, b) => api.patch(`/entries/${id}`, b),
  delete:  (id)    => api.delete(`/entries/${id}`),
};

// ── Watch History ────────────────────────────────────────────────────────────
export const watchApi = {
  list:   (entryId) => api.get(`/entries/${entryId}/watches`),
  add:    (entryId, body) => api.post(`/entries/${entryId}/watches`, body),
  delete: (entryId, watchId) => api.delete(`/entries/${entryId}/watches/${watchId}`),
};

// ── Notes ────────────────────────────────────────────────────────────────────
export const notesApi = {
  list:   (entryId) => api.get(`/entries/${entryId}/notes`),
  add:    (entryId, body) => api.post(`/entries/${entryId}/notes`, body),
  update: (entryId, noteId, body) => api.patch(`/entries/${entryId}/notes/${noteId}`, body),
  delete: (entryId, noteId) => api.delete(`/entries/${entryId}/notes/${noteId}`),
};

// ── Lists ────────────────────────────────────────────────────────────────────
export const listsApi = {
  list:   () => api.get('/lists'),
  create: (body) => api.post('/lists', body),
  get:    (id) => api.get(`/lists/${id}`),
  update: (id, body) => api.patch(`/lists/${id}`, body),
  delete: (id) => api.delete(`/lists/${id}`),
  addEntry:    (listId, entryId) => api.post(`/lists/${listId}/entries/${entryId}`),
  removeEntry: (listId, entryId) => api.delete(`/lists/${listId}/entries/${entryId}`),
};

// ── Tags ─────────────────────────────────────────────────────────────────────
export const tagsApi = {
  list:   () => api.get('/tags'),
  create: (name) => api.post('/tags', { name }),
  delete: (id) => api.delete(`/tags/${id}`),
  assign: (entryId, tagId) => api.post(`/entries/${entryId}/tags/${tagId}`),
  remove: (entryId, tagId) => api.delete(`/entries/${entryId}/tags/${tagId}`),
};

// ── Stats ────────────────────────────────────────────────────────────────────
export const statsApi = {
  overview: () => api.get('/stats'),
};

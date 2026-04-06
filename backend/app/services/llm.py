"""
LLM proxy service layer.

All AI calls in CinemaList go through here. The service is intentionally
LLM-agnostic: it speaks the OpenAI Chat Completions API format, which is
supported by OpenAI, Google Gemini (via the openai-compatible endpoint),
and local Ollama (via http://localhost:11434/v1).

Configuration (backend/.env)
-----------------------------
  LLM_API_KEY   = sk-...            # OpenAI key, Gemini key, or 'ollama'
  LLM_MODEL     = gpt-4o-mini       # or gemini-2.0-flash, llama3, etc.
  LLM_PROXY_URL = https://api.openai.com/v1  # or Gemini/Ollama URL

Public helpers
--------------
  chat(messages, max_tokens, temperature) -> str
      Low-level: send a list of {role, content} dicts, get a string back.

  recommend(entries)        -> list[dict]  -- personalised recommendations
  stats_report(stats)       -> str         -- narrative stats summary
  suggest_tags(movie)       -> list[str]   -- auto-tag suggestions
  nl_search(query, entries) -> list[dict]  -- natural language library search
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings


# ── Low-level chat completion ──────────────────────────────────────────────

async def chat(
    messages: list[dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    """
    Send a chat completion request to the configured LLM provider.

    Uses the OpenAI Chat Completions API format, which is compatible with
    OpenAI, Gemini (openai-compat), and Ollama.

    Raises HTTPException 503 when the LLM key is not configured.
    Raises HTTPException 502 when the upstream LLM returns an error.
    """
    if not settings.LLM_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "LLM not configured. Set LLM_API_KEY, LLM_MODEL, and LLM_PROXY_URL "
                "in backend/.env to enable AI features."
            ),
        )

    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    url = f"{settings.LLM_PROXY_URL.rstrip('/')}/chat/completions"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
        except httpx.ConnectError:
            raise HTTPException(
                status_code=502,
                detail=f"Could not connect to LLM at {settings.LLM_PROXY_URL}. "
                       "Check LLM_PROXY_URL in .env (or start Ollama if using local).",
            )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"LLM returned HTTP {resp.status_code}: {resp.text[:300]}",
        )

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected LLM response format: {exc}",
        )


# ── High-level AI helpers ─────────────────────────────────────────────────────

async def recommend(entries: list[dict[str, Any]]) -> list[dict]:
    """
    Generate personalised movie recommendations based on the user's watched list.

    `entries` should be a list of dicts with at least:
        title, year, rating (1-10), genres (list of str)

    Returns a list of recommendation dicts:
        [{"title": str, "year": int|None, "reason": str}, ...]
    """
    if not entries:
        return []

    # Build a compact watched list for the prompt (max 50 titles to stay in context)
    watched_lines = [
        f"- {e.get('title', '?')} ({e.get('year', '?')}) "
        f"— Bewertung: {e.get('rating') or 'nicht bewertet'}/10 "
        f"— Genre: {', '.join(e.get('genres', [])) or 'unbekannt'}"
        for e in entries[:50]
    ]
    watched_text = "\n".join(watched_lines)

    messages = [
        {
            "role": "system",
            "content": (
                "Du bist ein Filmexperte und Empfehlungssystem für eine persönliche Filmsammlung. "
                "Antworte ausschließlich mit einem JSON-Array. Keine zusätzliche Erklärung. "
                "Format: [{\"title\": \"Filmtitel\", \"year\": 2001, \"reason\": \"Kurze Begründung auf Deutsch\"}]"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Basierend auf meiner Filmliste empfehle mir 8 Filme, die ich noch nicht gesehen habe.\n\n"
                f"Meine gesehenen Filme:\n{watched_text}\n\n"
                "Gib mir 8 Empfehlungen als JSON-Array zurück."
            ),
        },
    ]

    raw = await chat(messages, max_tokens=1200, temperature=0.8)

    # Extract JSON array robustly (LLM may wrap in markdown ```json ... ```)
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        )

    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # If JSON parse fails, return a graceful error list
    return [{"title": "Fehler", "year": None, "reason": "LLM-Antwort konnte nicht geparst werden."}]


async def stats_report(stats: dict[str, Any]) -> str:
    """
    Generate a short narrative summary of the user's movie statistics.

    `stats` is the dict returned by GET /api/stats/.
    Returns a German prose paragraph (2-4 sentences).
    """
    stats_text = json.dumps(stats, ensure_ascii=False, indent=2)

    messages = [
        {
            "role": "system",
            "content": (
                "Du bist ein freundlicher Filmjournalist. "
                "Fasse die Filmstatistiken des Nutzers in 2-4 persönlichen, unterhaltsamen Sätzen auf Deutsch zusammen. "
                "Erwähne konkrete Zahlen. Kein Markdown, nur Fließtext."
            ),
        },
        {
            "role": "user",
            "content": f"Meine Filmstatistiken:\n{stats_text}\n\nBitte schreibe eine kurze Zusammenfassung.",
        },
    ]

    return await chat(messages, max_tokens=300, temperature=0.7)


async def suggest_tags(movie: dict[str, Any]) -> list[str]:
    """
    Suggest relevant tags for a movie based on its metadata.

    `movie` should contain: title, year, overview, genres (list of str),
    director, cast_top5 (list of str).

    Returns a list of 5-8 short German tag strings.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "Du bist ein Filmkatalogisierer. "
                "Schlage 5-8 kurze, relevante Tags für den Film vor. "
                "Tags sollen auf Deutsch sein, höchstens 3 Wörter pro Tag. "
                "Antworte ausschließlich mit einem JSON-Array von Strings. "
                "Beispiel: [\"Psycho-Thriller\", \"Mind-Bending\", \"Nonlineares Erzählen\"]"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Film: {movie.get('title')} ({movie.get('year')})\n"
                f"Genre: {', '.join(movie.get('genres', []))}\n"
                f"Regie: {movie.get('director', 'unbekannt')}\n"
                f"Besetzung: {', '.join(movie.get('cast_top5') or [])}\n"
                f"Inhalt: {movie.get('overview', 'kein Inhalt verfügbar')}\n\n"
                "Schlage 5-8 Tags als JSON-Array vor."
            ),
        },
    ]

    raw = await chat(messages, max_tokens=200, temperature=0.5)
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(line for line in lines if not line.strip().startswith("```"))

    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return [str(t) for t in result]
    except json.JSONDecodeError:
        pass

    return []


async def nl_search(query: str, entries: list[dict[str, Any]]) -> list[dict]:
    """
    Natural language search over the user's library.

    Examples:
        "Filme mit Brad Pitt die ich mit 8 oder höher bewertet habe"
        "Actionfilme aus den 90ern"
        "Etwas zum Lachen"

    `entries` is a list of entry dicts (title, year, rating, genres, director, notes).
    Returns a filtered + ranked subset of entries matching the query.
    """
    if not entries:
        return []

    # Compact library representation for the prompt
    library_lines = [
        f"{i+1}. {e.get('title')} ({e.get('year')}) | "
        f"Bewertung: {e.get('rating') or '-'} | "
        f"Genre: {', '.join(e.get('genres', []))} | "
        f"Regie: {e.get('director', '-')}"
        for i, e in enumerate(entries[:100])
    ]
    library_text = "\n".join(library_lines)

    messages = [
        {
            "role": "system",
            "content": (
                "Du bist ein intelligentes Filmsuchsystem für eine persönliche Filmsammlung. "
                "Der Nutzer stellt eine natürlichsprachige Suchanfrage. "
                "Gib die Nummern der passenden Filme als JSON-Array zurück. "
                "Nur Zahlen im Array. Beispiel: [3, 7, 12]. Keine Erklärung."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Meine Filmbibliothek:\n{library_text}\n\n"
                f"Suchanfrage: \"{query}\"\n\n"
                "Welche Nummern passen? Gib ein JSON-Array zurück."
            ),
        },
    ]

    raw = await chat(messages, max_tokens=300, temperature=0.3)
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(line for line in lines if not line.strip().startswith("```"))

    try:
        indices = json.loads(raw)
        if isinstance(indices, list):
            # Convert 1-based indices back to entries
            results = []
            for idx in indices:
                if isinstance(idx, int) and 1 <= idx <= len(entries):
                    results.append(entries[idx - 1])
            return results
    except json.JSONDecodeError:
        pass

    return []

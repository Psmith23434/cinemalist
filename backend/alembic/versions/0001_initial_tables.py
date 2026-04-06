"""initial tables

Revision ID: 0001
Revises:
Create Date: 2026-04-05

Creates all tables for CinemaList Phase 2:
  movies, genres, movie_genres,
  entries, watch_events, notes (inline on entry),
  tags, entry_tags,
  lists, list_items,
  tmdb_cache, sync_log
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── genres ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "genres",
        sa.Column("id",      sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tmdb_id", sa.Integer(), unique=True, nullable=True),
        sa.Column("name",    sa.String(100), nullable=False),
    )
    op.create_index("ix_genres_name", "genres", ["name"])

    # ── movies ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        "movies",
        sa.Column("id",             sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid",           sa.String(36), unique=True, nullable=False),

        # TMDb identifiers
        sa.Column("tmdb_id",        sa.Integer(), unique=True, nullable=True),
        sa.Column("imdb_id",        sa.String(20), nullable=True),

        # Core metadata
        sa.Column("title",          sa.String(500), nullable=False),
        sa.Column("original_title", sa.String(500), nullable=True),
        sa.Column("year",           sa.Integer(), nullable=True),
        sa.Column("overview",       sa.Text(), nullable=True),
        sa.Column("tagline",        sa.String(500), nullable=True),
        sa.Column("runtime",        sa.Integer(), nullable=True),
        sa.Column("language",       sa.String(10), nullable=True),
        sa.Column("status",         sa.String(50), nullable=True),

        # TMDb community ratings
        sa.Column("tmdb_rating",     sa.Float(), nullable=True),
        sa.Column("tmdb_vote_count", sa.Integer(), nullable=True),

        # Images
        sa.Column("poster_path",       sa.String(500), nullable=True),
        sa.Column("backdrop_path",     sa.String(500), nullable=True),
        sa.Column("local_poster_path", sa.String(500), nullable=True),

        # People (denormalised for v1 simplicity)
        sa.Column("director",  sa.String(300), nullable=True),
        sa.Column("cast_top5", sa.Text(), nullable=True),

        # Timestamps
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_movies_tmdb_id", "movies", ["tmdb_id"])
    op.create_index("ix_movies_title",   "movies", ["title"])
    op.create_index("ix_movies_year",    "movies", ["year"])

    # ── movie_genres (many-to-many) ──────────────────────────────────────────────────────
    op.create_table(
        "movie_genres",
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre_id", sa.Integer(), sa.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
    )

    # ── entries ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "entries",
        sa.Column("id",   sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.String(36), unique=True, nullable=False),

        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),

        # User data
        sa.Column("rating",         sa.Float(), nullable=True),
        sa.Column("notes",          sa.Text(), nullable=True),
        sa.Column("review",         sa.Text(), nullable=True),
        sa.Column("is_favorite",    sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_watchlisted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("watched",        sa.Boolean(), nullable=False, server_default=sa.true()),

        # Watch dates
        sa.Column("first_watched_at", sa.DateTime(), nullable=True),
        sa.Column("last_watched_at",  sa.DateTime(), nullable=True),

        # Timestamps + soft-delete
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_entries_movie_id",   "entries", ["movie_id"])
    op.create_index("ix_entries_updated_at", "entries", ["updated_at"])

    # ── watch_events ───────────────────────────────────────────────────────────────────
    op.create_table(
        "watch_events",
        sa.Column("id",       sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid",     sa.String(36), unique=True, nullable=False),
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("watched_at", sa.DateTime(), nullable=True),
        sa.Column("platform",   sa.String(100), nullable=True),
        sa.Column("note",       sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_watch_events_entry_id", "watch_events", ["entry_id"])

    # ── tags ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        "tags",
        sa.Column("id",   sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
    )
    op.create_index("ix_tags_name", "tags", ["name"])

    # ── entry_tags (many-to-many) ─────────────────────────────────────────────────────────
    op.create_table(
        "entry_tags",
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id",   sa.Integer(), sa.ForeignKey("tags.id",    ondelete="CASCADE"), primary_key=True),
    )

    # ── lists ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "lists",
        sa.Column("id",             sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid",           sa.String(36), unique=True, nullable=False),
        sa.Column("name",           sa.String(200), nullable=False),
        sa.Column("description",    sa.Text(), nullable=True),
        sa.Column("is_public",      sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cover_movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at",     sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",     sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # ── list_items ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "list_items",
        sa.Column("list_id",  sa.Integer(), sa.ForeignKey("lists.id",   ondelete="CASCADE"), primary_key=True),
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("added_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # ── tmdb_cache ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "tmdb_cache",
        sa.Column("id",         sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cache_key",  sa.String(300), unique=True, nullable=False),
        sa.Column("data_json",  sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_tmdb_cache_key",        "tmdb_cache", ["cache_key"])
    op.create_index("ix_tmdb_cache_expires_at", "tmdb_cache", ["expires_at"])

    # ── sync_log ───────────────────────────────────────────────────────────────────────
    op.create_table(
        "sync_log",
        sa.Column("id",           sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id",    sa.String(100), nullable=False),
        sa.Column("table_name",   sa.String(100), nullable=False),
        sa.Column("record_uuid",  sa.String(36),  nullable=False),
        sa.Column("action",       sa.String(20),  nullable=False),
        sa.Column("synced_at",    sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
    )
    op.create_index("ix_sync_log_device_id",   "sync_log", ["device_id"])
    op.create_index("ix_sync_log_record_uuid", "sync_log", ["record_uuid"])


def downgrade() -> None:
    op.drop_table("sync_log")
    op.drop_table("tmdb_cache")
    op.drop_table("list_items")
    op.drop_table("lists")
    op.drop_table("entry_tags")
    op.drop_table("tags")
    op.drop_table("watch_events")
    op.drop_table("entries")
    op.drop_table("movie_genres")
    op.drop_table("movies")
    op.drop_table("genres")

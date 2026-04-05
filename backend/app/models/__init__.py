# Import all models here so Alembic autogenerate picks them up
from app.models.movie import Movie
from app.models.genre import Genre
from app.models.movie_genre import MovieGenre
from app.models.entry import Entry
from app.models.watch_event import WatchEvent
from app.models.tag import Tag
from app.models.entry_tag import EntryTag
from app.models.list import MovieList
from app.models.list_item import ListItem
from app.models.tmdb_cache import TmdbCache
from app.models.sync_log import SyncLog

import { useState, useEffect } from 'react';
import {
  Grid, TextInput, Select, Group, Loader, Center,
  SegmentedControl, Box,
} from '@mantine/core';
import { IconSearch, IconMovie } from '@tabler/icons-react';
import { api } from '../api/client';
import PosterCard from '../components/PosterCard';
import EmptyState from '../components/EmptyState';

export default function LibraryPage() {
  const [entries, setEntries]   = useState([]);
  const [genres,  setGenres]    = useState([]);
  const [loading, setLoading]   = useState(true);
  const [search,  setSearch]    = useState('');
  const [genre,   setGenre]     = useState(null);
  const [sort,    setSort]      = useState('updated_at');
  const [fav,     setFav]       = useState('all');

  useEffect(() => {
    api.getGenres().then(g => setGenres(g.map(x => ({ value: String(x.id), label: x.name }))));
  }, []);

  useEffect(() => {
    setLoading(true);
    // Fix bug 4: use per_page (not limit) to match PaginatedResponse backend param
    // Fix bug 4: use is_favorite (not favourites) for the favourite filter
    const params = { per_page: 100 };
    if (genre)         params.genre_id    = genre;
    if (fav === 'fav') params.is_favorite = true;
    api.getEntries(params)
      .then(data => setEntries(Array.isArray(data) ? data : data.items ?? []))
      .finally(() => setLoading(false));
  }, [genre, sort, fav]);

  // Client-side text filter + sort (avoids extra round-trips for search-as-you-type)
  const filtered = entries
    .filter(e => !search || (e.movie?.title ?? '').toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sort === 'rating')     return (b.rating ?? 0) - (a.rating ?? 0);
      if (sort === 'created_at') return new Date(b.created_at) - new Date(a.created_at);
      // default: last updated / watch date
      return new Date(b.updated_at) - new Date(a.updated_at);
    });

  return (
    <Box>
      <Group mb="md" gap="sm" wrap="wrap">
        <TextInput
          placeholder="Filter library…"
          leftSection={<IconSearch size={14} />}
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: 180 }}
          styles={{ input: { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' } }}
        />
        <Select
          placeholder="Genre"
          data={[{ value: '', label: 'All genres' }, ...genres]}
          value={genre ?? ''}
          onChange={v => setGenre(v || null)}
          clearable
          styles={{ input: { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' } }}
        />
        <Select
          data={[
            { value: 'updated_at', label: 'Recently updated' },
            { value: 'rating',     label: 'Rating' },
            { value: 'created_at', label: 'Date added' },
          ]}
          value={sort}
          onChange={setSort}
          styles={{ input: { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' } }}
        />
        <SegmentedControl
          value={fav}
          onChange={setFav}
          data={[{ value: 'all', label: 'All' }, { value: 'fav', label: '★ Favs' }]}
          styles={{ root: { background: '#242424' }, label: { color: '#b8b8b8' } }}
        />
      </Group>

      {loading ? (
        <Center py={80}><Loader color="yellow" /></Center>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={IconMovie}
          title="Your library is empty"
          description="Search for a movie and add it to start building your collection."
        />
      ) : (
        <Grid gutter="md">
          {filtered.map(e => (
            <Grid.Col key={e.id} span={{ base: 6, xs: 4, sm: 3, md: 2 }}>
              <PosterCard entry={e} />
            </Grid.Col>
          ))}
        </Grid>
      )}
    </Box>
  );
}

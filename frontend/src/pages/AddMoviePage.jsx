import { useState, useCallback } from 'react';
import {
  Title, TextInput, Loader, Center, Stack, Text, Card,
  Image, Group, Button, Badge, Box, ActionIcon,
} from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconSearch, IconPlus, IconCheck } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { moviesApi, entriesApi } from '../api/client';
import { useEffect } from 'react';

const POSTER_BASE = 'https://image.tmdb.org/t/p/w185';

export default function AddMoviePage() {
  const [query, setQuery] = useState('');
  const [debounced] = useDebouncedValue(query, 400);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!debounced.trim()) { setResults([]); return; }
    setLoading(true);
    moviesApi.search(debounced)
      .then(data => setResults(Array.isArray(data) ? data : data.results || []))
      .catch(err => notifications.show({ color: 'red', message: err.message }))
      .finally(() => setLoading(false));
  }, [debounced]);

  const handleAdd = async (tmdbMovie, asWatchlist = false) => {
    setAdding(tmdbMovie.id);
    try {
      // 1. Import / cache the movie
      await moviesApi.import(tmdbMovie.id);
      // 2. Create entry
      const entry = await entriesApi.create({
        tmdb_id: tmdbMovie.id,
        status: asWatchlist ? 'watchlist' : 'watched',
      });
      notifications.show({
        color: 'yellow',
        icon: <IconCheck size={16} />,
        message: `"${tmdbMovie.title}" added to your ${asWatchlist ? 'watchlist' : 'library'}!`,
      });
      if (!asWatchlist) navigate(`/movie/${entry.id}`);
    } catch (err) {
      notifications.show({ color: 'red', message: err.message });
    } finally {
      setAdding(null);
    }
  };

  const year = (d) => d ? d.slice(0, 4) : '?';

  return (
    <>
      <Title order={2} mb="lg" style={{ color: '#C9C9C9' }}>Add a Movie</Title>

      <TextInput
        placeholder="Search TMDb — type a title…"
        leftSection={<IconSearch size={16} />}
        rightSection={loading ? <Loader size={14} color="yellow" /> : null}
        value={query}
        onChange={e => setQuery(e.target.value)}
        size="md"
        mb="lg"
        autoFocus
        styles={{ input: { background: '#1a1a1a', border: '1px solid #424242', color: '#C9C9C9', fontSize: 15 } }}
      />

      {results.length === 0 && !loading && debounced && (
        <Center h={200}>
          <Text c="dimmed">No results for "{debounced}"</Text>
        </Center>
      )}

      <Stack gap="sm">
        {results.map(movie => (
          <Card
            key={movie.id}
            padding="sm"
            radius="lg"
            style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}
          >
            <Group gap="md" wrap="nowrap">
              {/* Poster thumbnail */}
              <Box style={{ flexShrink: 0, width: 52, height: 78, borderRadius: 6, overflow: 'hidden', background: '#242424' }}>
                {movie.poster_path ? (
                  <Image
                    src={`${POSTER_BASE}${movie.poster_path}`}
                    alt={movie.title}
                    w={52} h={78}
                    style={{ objectFit: 'cover' }}
                  />
                ) : null}
              </Box>

              {/* Info */}
              <Box style={{ flex: 1, minWidth: 0 }}>
                <Text fw={600} size="sm" lineClamp={1} style={{ color: '#C9C9C9' }}>
                  {movie.title}
                </Text>
                <Group gap="xs" mt={2}>
                  <Text size="xs" c="dimmed">{year(movie.release_date)}</Text>
                  {movie.vote_average > 0 && (
                    <Badge size="xs" color="yellow" variant="light">
                      ★ {movie.vote_average.toFixed(1)}
                    </Badge>
                  )}
                </Group>
                {movie.overview && (
                  <Text size="xs" c="dimmed" lineClamp={2} mt={4}>
                    {movie.overview}
                  </Text>
                )}
              </Box>

              {/* Actions */}
              <Group gap="xs" style={{ flexShrink: 0 }}>
                <Button
                  size="xs"
                  color="yellow"
                  leftSection={<IconPlus size={14} />}
                  loading={adding === movie.id}
                  onClick={() => handleAdd(movie, false)}
                >
                  Add
                </Button>
                <Button
                  size="xs"
                  variant="light"
                  loading={adding === movie.id}
                  onClick={() => handleAdd(movie, true)}
                >
                  Watchlist
                </Button>
              </Group>
            </Group>
          </Card>
        ))}
      </Stack>
    </>
  );
}

import { useState } from 'react';
import {
  TextInput, Button, Grid, Card, Image, Text, Box,
  Group, Loader, Center, Stack, Alert,
} from '@mantine/core';
import { IconSearch, IconPlus, IconCheck, IconAlertCircle, IconBook } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';
import { api, posterUrl } from '../api/client';

export default function AddMoviePage() {
  const [query,     setQuery]     = useState('');
  const [results,   setResults]   = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [importing, setImporting] = useState(null);
  const [error,     setError]     = useState('');
  const navigate = useNavigate();

  async function search() {
    if (!query.trim()) return;
    setLoading(true); setError('');
    try {
      const data = await api.searchTmdb(query);
      setResults(data.results ?? []);
      if ((data.results ?? []).length === 0) setError('No results found.');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function importMovie(tmdbId, title) {
    setImporting(tmdbId);
    try {
      // Step 1: import (or retrieve cached) movie from TMDb
      const movie = await api.importTmdb(tmdbId);

      // Step 2: try to create an entry — backend returns 409 if one already exists
      let entry;
      try {
        entry = await api.createEntry({ movie_id: movie.id });
        notifications.show({
          title: 'Added!',
          message: `${movie.title} added to your library.`,
          color: 'yellow',
          icon: <IconCheck size={16} />,
        });
      } catch (createErr) {
        // Fix bug 7: 409 = already in library — find the existing entry and navigate to it
        if (createErr.message.includes('already exists') || createErr.message.includes('409')) {
          const existing = await api.getEntries({ per_page: 200 });
          const items = Array.isArray(existing) ? existing : existing.items ?? [];
          const found = items.find(e => e.movie_id === movie.id || e.movie?.id === movie.id);
          notifications.show({
            title: 'Already in library',
            message: `${movie.title} is already in your library.`,
            color: 'blue',
            icon: <IconBook size={16} />,
          });
          if (found) { navigate(`/movie/${found.id}`); return; }
          // Fallback: go to library if we can't pin down the entry id
          navigate('/');
          return;
        }
        throw createErr; // re-throw any other error
      }

      navigate(`/movie/${entry.id}`);
    } catch (e) {
      notifications.show({
        title: 'Error',
        message: e.message,
        color: 'red',
        icon: <IconAlertCircle size={16} />,
      });
    } finally {
      setImporting(null);
    }
  }

  return (
    <Box maw={860} mx="auto">
      <Text fw={700} size="xl" mb="md" style={{ color: '#e2b04a' }}>Add a Movie</Text>

      <Group mb="lg" gap="sm">
        <TextInput
          placeholder="Search TMDb — e.g. Blade Runner"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
          style={{ flex: 1 }}
          styles={{ input: { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' } }}
          leftSection={<IconSearch size={14} />}
        />
        <Button onClick={search} loading={loading} color="yellow" variant="filled">
          Search
        </Button>
      </Group>

      {error && <Alert color="red" mb="md" icon={<IconAlertCircle />}>{error}</Alert>}

      {loading ? (
        <Center py={60}><Loader color="yellow" /></Center>
      ) : (
        <Grid gutter="md">
          {results.map(r => (
            <Grid.Col key={r.id} span={{ base: 6, sm: 4, md: 3 }}>
              <Card
                shadow="sm" radius="lg"
                style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}
              >
                <Card.Section>
                  {posterUrl(r.poster_path) ? (
                    <Image src={posterUrl(r.poster_path)} height={220} fit="cover" />
                  ) : (
                    <Box style={{
                      height: 220, background: '#242424',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Text c="dimmed" size="xs">No poster</Text>
                    </Box>
                  )}
                </Card.Section>
                <Stack gap={4} p="xs" pt="sm">
                  <Text fw={600} size="sm" lineClamp={2} style={{ color: '#e8e8e8' }}>{r.title}</Text>
                  <Text size="xs" c="dimmed">{r.release_date?.slice(0, 4) ?? '\u2014'}</Text>
                  <Button
                    size="xs"
                    color="yellow"
                    variant="light"
                    leftSection={<IconPlus size={12} />}
                    loading={importing === r.id}
                    onClick={() => importMovie(r.id, r.title)}
                    mt={4}
                  >
                    Add
                  </Button>
                </Stack>
              </Card>
            </Grid.Col>
          ))}
        </Grid>
      )}
    </Box>
  );
}

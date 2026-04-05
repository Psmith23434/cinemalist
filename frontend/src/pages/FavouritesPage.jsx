import { useState, useEffect, useCallback } from 'react';
import { Title, Text, SimpleGrid, Loader, Center, Stack, Group, ActionIcon, Tooltip } from '@mantine/core';
import { IconHeart, IconRefresh } from '@tabler/icons-react';
import { entriesApi } from '../api/client';
import MovieCard from '../components/MovieCard';

export default function FavouritesPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await entriesApi.list({ is_favorite: true, sort_by: 'rating', sort_dir: 'desc' });
      setEntries(data);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <>
      <Group justify="space-between" mb="lg">
        <Stack gap={0}>
          <Title order={2} style={{ color: '#C9C9C9' }}>Favourites</Title>
          <Text size="sm" c="dimmed">{entries.length} film{entries.length !== 1 ? 's' : ''}</Text>
        </Stack>
        <Tooltip label="Refresh"><ActionIcon variant="subtle" onClick={load} aria-label="Refresh"><IconRefresh size={16} /></ActionIcon></Tooltip>
      </Group>
      {loading ? <Center h={300}><Loader color="yellow" /></Center>
        : entries.length === 0 ? (
          <Center h={300}><Stack align="center"><IconHeart size={48} color="#424242" /><Text c="dimmed">No favourites yet — heart a film to add it here.</Text></Stack></Center>
        ) : (
          <SimpleGrid cols={{ base: 2, xs: 3, sm: 4, md: 5, lg: 6 }} spacing="md">
            {entries.map(e => <MovieCard key={e.id} entry={e} onUpdate={load} />)}
          </SimpleGrid>
        )}
    </>
  );
}

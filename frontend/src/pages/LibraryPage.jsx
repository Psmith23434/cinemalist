import { useState, useEffect, useCallback } from 'react';
import {
  Title, Text, SimpleGrid, Loader, Center, Stack,
  Group, Badge, ActionIcon, Tooltip,
} from '@mantine/core';
import { IconMovie, IconRefresh } from '@tabler/icons-react';
import { entriesApi } from '../api/client';
import MovieCard from '../components/MovieCard';
import FilterBar from '../components/FilterBar';

const DEFAULT_FILTERS = {
  query: '', genre: '', sortBy: 'added_at', sortDir: 'desc', status: 'watched',
};

export default function LibraryPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        q:        filters.query   || undefined,
        genre:    filters.genre   || undefined,
        sort_by:  filters.sortBy,
        sort_dir: filters.sortDir,
        status:   filters.status !== 'all' ? filters.status : undefined,
      };
      const data = await entriesApi.list(params);
      setEntries(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  return (
    <>
      <Group justify="space-between" mb="md">
        <Stack gap={0}>
          <Title order={2} style={{ color: '#C9C9C9' }}>My Library</Title>
          <Text size="sm" c="dimmed">{entries.length} film{entries.length !== 1 ? 's' : ''}</Text>
        </Stack>
        <Tooltip label="Refresh">
          <ActionIcon variant="subtle" onClick={load} aria-label="Refresh library">
            <IconRefresh size={16} />
          </ActionIcon>
        </Tooltip>
      </Group>

      <FilterBar filters={filters} onChange={setFilters} />

      {loading ? (
        <Center h={300}><Loader color="yellow" /></Center>
      ) : entries.length === 0 ? (
        <Center h={300}>
          <Stack align="center" gap="sm">
            <IconMovie size={48} color="#424242" />
            <Text c="dimmed">No movies yet. Add your first film!</Text>
          </Stack>
        </Center>
      ) : (
        <SimpleGrid
          cols={{ base: 2, xs: 3, sm: 4, md: 5, lg: 6, xl: 7 }}
          spacing="md"
        >
          {entries.map(e => (
            <MovieCard key={e.id} entry={e} onUpdate={load} />
          ))}
        </SimpleGrid>
      )}
    </>
  );
}

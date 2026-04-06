import { useState, useEffect } from 'react';
import { Grid, Text, Loader, Center, Box } from '@mantine/core';
import { IconClock } from '@tabler/icons-react';
import { api } from '../api/client';
import PosterCard from '../components/PosterCard';
import EmptyState from '../components/EmptyState';

export default function WatchlistPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fix bug 4: backend param is is_watchlisted (not 'watchlist'), per_page not limit
    api.getEntries({ is_watchlisted: true, per_page: 100 })
      .then(data => setEntries(Array.isArray(data) ? data : data.items ?? []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Box>
      <Text fw={700} size="xl" mb="md" style={{ color: '#e2b04a' }}>Watchlist</Text>
      {loading ? (
        <Center py={80}><Loader color="yellow" /></Center>
      ) : entries.length === 0 ? (
        <EmptyState
          icon={IconClock}
          title="Your watchlist is empty"
          description="Mark a movie as 'Want to watch' to add it here."
        />
      ) : (
        <Grid gutter="md">
          {entries.map(e => (
            <Grid.Col key={e.id} span={{ base: 6, xs: 4, sm: 3, md: 2 }}>
              <PosterCard entry={e} />
            </Grid.Col>
          ))}
        </Grid>
      )}
    </Box>
  );
}

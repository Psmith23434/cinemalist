import { useState, useEffect } from 'react';
import { Grid, Text, Loader, Center, Box } from '@mantine/core';
import { IconHeart } from '@tabler/icons-react';
import { api } from '../api/client';
import PosterCard from '../components/PosterCard';
import EmptyState from '../components/EmptyState';

export default function FavouritesPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fix bug 3: backend param is is_favorite (not 'favourites'), per_page not limit
    api.getEntries({ is_favorite: true, per_page: 100 })
      .then(data => setEntries(Array.isArray(data) ? data : data.items ?? []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Box>
      <Text fw={700} size="xl" mb="md" style={{ color: '#e2b04a' }}>Favourites</Text>
      {loading ? (
        <Center py={80}><Loader color="yellow" /></Center>
      ) : entries.length === 0 ? (
        <EmptyState
          icon={IconHeart}
          title="No favourites yet"
          description="Open any movie and toggle the heart to mark it as a favourite."
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

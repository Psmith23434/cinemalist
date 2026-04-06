import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Text, Group, Button, Grid, Loader, Center, Badge, ActionIcon, Stack,
} from '@mantine/core';
import { IconArrowLeft, IconTrash } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { api } from '../api/client';
import PosterCard from '../components/PosterCard';
import EmptyState from '../components/EmptyState';
import { IconList } from '@tabler/icons-react';

export default function ListDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [list,    setList]    = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getList(id)
      .then(setList)
      .catch(() => notifications.show({ message: 'Could not load list.', color: 'red' }))
      .finally(() => setLoading(false));
  }, [id]);

  async function removeItem(entryId) {
    try {
      await api.removeFromList(id, entryId);
      setList(prev => ({
        ...prev,
        items: prev.items.filter(item => item.entry?.id !== entryId),
      }));
    } catch (e) {
      notifications.show({ message: e.message, color: 'red' });
    }
  }

  if (loading) return <Center py={80}><Loader color="yellow" /></Center>;
  if (!list)   return <Text c="red">List not found.</Text>;

  const entries = (list.items ?? []).map(item => item.entry).filter(Boolean);

  return (
    <Box>
      <Group mb="lg" justify="space-between">
        <Button
          variant="subtle" color="gray" size="sm"
          leftSection={<IconArrowLeft size={14} />}
          onClick={() => navigate('/lists')}
        >
          All lists
        </Button>
        <Badge color="gray" variant="outline">{entries.length} film{entries.length !== 1 ? 's' : ''}</Badge>
      </Group>

      <Text fw={700} size="xl" mb={4} style={{ color: '#e2b04a' }}>{list.name}</Text>
      {list.description && <Text c="dimmed" size="sm" mb="lg">{list.description}</Text>}

      {entries.length === 0 ? (
        <EmptyState
          icon={IconList}
          title="This list is empty"
          description="Add movies to this list from their detail page."
        />
      ) : (
        <Grid gutter="md">
          {entries.map(e => (
            <Grid.Col key={e.id} span={{ base: 6, xs: 4, sm: 3, md: 2 }}>
              <Stack gap={4}>
                <PosterCard entry={e} />
                <ActionIcon
                  color="red" variant="subtle" size="sm"
                  onClick={() => removeItem(e.id)}
                  style={{ alignSelf: 'flex-end' }}
                >
                  <IconTrash size={13} />
                </ActionIcon>
              </Stack>
            </Grid.Col>
          ))}
        </Grid>
      )}
    </Box>
  );
}
